from datetime import datetime, time, timedelta
import time as time_module
import os
import pytz
from django.conf import settings
from django.db import connections  # Use Django's connection pool
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'results', 'morning_report')
os.makedirs(REPORTS_DIR, exist_ok=True)


def format_report_data(from_epoch, to_epoch, from_date_str, to_date_str, query, results, execution_time):
    """
    Identical to your original function — no changes.
    """
    total_records = sum(row[1] for row in results)

    content_lines = [
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
        content_lines.append(f'| {row[0]:<13} | {int(row[1]):<6} |')

    content_lines.extend([
        '+---------------+--------+',
        '',
        f'{len(results)} rows in set ({execution_time} sec)',
        '',
        f'Total = {total_records} records'
    ])

    return '\n'.join(content_lines)


def generate_daily_report_file():
    """
    Generates report and saves to reports/results/morning_report/
    Using Django's federated database connection with script credentials.
    """
    try:
        # --- 1. Dynamic Time Calculation (IST-aware) ---
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        to_dt = datetime.combine(now_ist.date(), time(10, 0, 0)).replace(tzinfo=ist)
        from_dt = to_dt - timedelta(days=1)

        to_epoch = int(to_dt.timestamp() * 1000)
        from_epoch = int(from_dt.timestamp() * 1000)

        from_date_str = from_dt.strftime("%d %B %Y")
        to_date_str = to_dt.strftime("%d %B %Y")

    except Exception as e:
        print(f"Time calculation error: {e}")
        return

    # --- 2. Query FederatedSearch using Django's 'federated' connection ---
    query = f'select type, sum(records) as sum from collectionsMetaData where DATETIME between "{from_epoch}" and "{to_epoch}" group by type order by sum DESC;'

    results = []
    execution_time = 0.0

    try:
        # Use the 'federated' database connection (credentials from script)
        with connections['federated'].cursor() as cursor:
            start_time = time_module.time()
            cursor.execute(query)
            results = cursor.fetchall()
            execution_time = round(time_module.time() - start_time, 3)

    except Exception as e:
        print(f"Database error: {e}")
        return

    # --- 3. Format Report ---
    try:
        report_content = format_report_data(
            from_epoch=str(from_epoch),
            to_epoch=str(to_epoch),
            from_date_str=from_date_str,
            to_date_str=to_date_str,
            query=query,
            results=results,
            execution_time=execution_time
        )
    except Exception as e:
        print(f"Formatting error: {e}")
        return

    filename = f"24H_{from_dt.strftime('%d')}-{to_dt.strftime('%d_%b_%Y')}.txt"
    file_path = os.path.join(REPORTS_DIR, 'results', 'morning_report', filename)

    try:
        with open(file_path, "w", encoding='utf-8') as f:
            f.write(report_content)
        print(f"✓ Report saved: {file_path}")
    except IOError as io_err:
        print(f"File write error: {io_err}")