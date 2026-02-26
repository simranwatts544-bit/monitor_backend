# backend/apps/reports/views.py
import os
import time
from datetime import datetime, time as dt_time, timedelta
import pytz
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes  # ✅ Added
from rest_framework.permissions import AllowAny  # ✅ Added
from rest_framework import status
from django.http import HttpResponse, Http404
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Path relative to this file
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'results', 'report')
os.makedirs(REPORTS_DIR, exist_ok=True)


def format_report_data(from_epoch, to_epoch, from_date_str, to_date_str, query, results, execution_time):
    total_records = sum(row[1] for row in results)
    lines = [
        f'from="{from_epoch}"',
        f'to="{to_epoch}"',
        '',
        f'from= {from_date_str}',
        '',
        f'to= {to_date_str}',
        '',
        f'{query}',
        '',
        '+---------------+--------+',
        '| type          | sum    |',
        '+---------------+--------+',
    ]
    for row in results:
        lines.append(f'| {row[0]:<13} | {int(row[1]):<6} |')
    lines.extend([
        '+---------------+--------+',
        '',
        f'{len(results)} rows in set ({execution_time} sec)',
        '',
        f'Total = {total_records} records'
    ])
    return '\n'.join(lines)


class ReportListView(APIView):
    def get(self, request):
        files = [f for f in os.listdir(REPORTS_DIR) if f.endswith('.txt')]
        reports = []
        for fname in files:
            fp = os.path.join(REPORTS_DIR, fname)
            stat = os.stat(fp)
            
            # Parse total records from file
            total = 0
            with open(fp, 'r') as f:
                for line in reversed(f.readlines()):
                    if line.startswith('Total = ') and line.endswith(' records'):
                        try:
                            total = int(line.split()[2])
                        except:
                            pass
                        break
            
            reports.append({
                "name": fname,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "total_records": total
            })
        return Response({"reports": reports})

@api_view(['GET', 'POST'])
def get_custom_report(request):
    """Generate custom report - GET for download, POST to save & list"""
    
    # ✅ Handle both GET (query params) and POST (JSON body)
    if request.method == 'GET':
        from_epoch = request.GET.get('from_epoch')
        to_epoch = request.GET.get('to_epoch')
    else:  # POST
        from_epoch = request.data.get('from_epoch')
        to_epoch = request.data.get('to_epoch')
    
    if not from_epoch or not to_epoch:
        return Response({"error": "Missing from_epoch or to_epoch"}, status=400)
    
    try:
        from_epoch = int(from_epoch)
        to_epoch = int(to_epoch)
        if from_epoch >= to_epoch:
            return Response({"error": "from_epoch must be < to_epoch"}, status=400)
        
        from_dt = datetime.fromtimestamp(from_epoch / 1000)
        to_dt = datetime.fromtimestamp(to_epoch / 1000)
        from_date_str = from_dt.strftime("%d %B %Y")
        to_date_str = to_dt.strftime("%d %B %Y")
        
        query = f'select type, sum(records) as sum from collectionsMetaData where DATETIME between "{from_epoch}" and "{to_epoch}" group by type order by sum DESC;'
        
        with connections['federated'].cursor() as cursor:
            start = time.time()
            cursor.execute(query)
            results = cursor.fetchall()
            exec_time = round(time.time() - start, 3)
        
        content = format_report_data(
            str(from_epoch), str(to_epoch),
            from_date_str, to_date_str,
            query, results, exec_time
        )
        
        filename = f"custom_{from_dt.strftime('%d%b%Y')}_to_{to_dt.strftime('%d%b%Y')}.txt"
        
        # ✅ If POST request, SAVE the file to reports directory
        if request.method == 'POST':
            import os
            # Adjust this path to match your reports directory
            reports_dir = REPORTS_DIR
            os.makedirs(reports_dir, exist_ok=True)
            filepath = os.path.join(reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Calculate total records
            total_records = sum(int(row[1]) for row in results)
            
            # Return JSON response for frontend to refresh list
            return Response({
                "status": "success",
                "filename": filename,
                "created_at": datetime.now().isoformat(),
                "size": os.path.getsize(filepath),
                "total_records": total_records
            }, status=201)
        
        # ✅ If GET request, return as download (existing behavior)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)

class GenerateDailyReportView(APIView):
    permission_classes = [AllowAny]  # Allows unauthenticated access
    
    def post(self, request):
        try:
            # Your existing logic here (copy from your current function)
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            to_dt = datetime.combine(now_ist.date(), dt_time(10, 0, 0)).replace(tzinfo=ist)
            from_dt = to_dt - timedelta(days=1)
            
            to_epoch = int(to_dt.timestamp() * 1000)
            from_epoch = int(from_dt.timestamp() * 1000)
            from_date_str = from_dt.strftime("%d %B %Y")
            to_date_str = to_dt.strftime("%d %B %Y")
            
            query = f'select type, sum(records) as sum from collectionsMetaData where DATETIME between "{from_epoch}" and "{to_epoch}" group by type order by sum DESC;'
            
            with connections['federated'].cursor() as cursor:
                start = time.time()
                cursor.execute(query)
                results = cursor.fetchall()
                exec_time = round(time.time() - start, 3)
            
            content = format_report_data(
                str(from_epoch), str(to_epoch),
                from_date_str, to_date_str,
                query, results, exec_time
            )
            
            filename = f"24H_{from_dt.strftime('%d')}-{to_dt.strftime('%d_%b_%Y')}.txt"
            filepath = os.path.join(REPORTS_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return Response({
                "message": "Success",
                "filename": filename
            }, status=200)
            
        except Exception as e:
            return Response({"error": str(e)}, status=500)


@api_view(['GET'])
def get_report_data(request, filename):
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        return Response({"error": "Not found"}, status=404)
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Parse total records from last line: "Total = X records"
    total_records = 0
    lines = content.split('\n')
    for line in reversed(lines):
        if line.startswith('Total = ') and line.endswith(' records'):
            try:
                total_records = int(line.split(' = ')[1].split(' ')[0])
                break
            except:
                pass
    
    # Parse table data
    data = []
    in_table = False
    for line in lines:
        line = line.strip()
        if '| type' in line and '| sum' in line:
            in_table = True
            continue
        if in_table and line.startswith('|') and '|' in line and not line.startswith('+'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3 and parts[1] and parts[2].isdigit():
                data.append({"type": parts[1], "sum": int(parts[2])})
        elif in_table and 'rows in set' in line:
            break

    return Response({
        "content": content,
        "data": data,
        "total_records": total_records  # ✅ Now real number
    })


# ✅ NEW: Serve raw report file for direct download (fixes HTML issue)
def serve_report_file(request, filename):
    """
    Serve raw report file for direct download.
    This prevents React SPA from intercepting the request and returning index.html
    """
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        raise Http404("File not found")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response