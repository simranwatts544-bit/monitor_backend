import time
from datetime import datetime
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from elasticsearch import Elasticsearch
from django.conf import settings
import pytz

class MonitoringViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_es_client(self):
        try:
            es_host = getattr(settings, 'ELASTICSEARCH_HOST', 'http://142.198.63.54:9200')
            return Elasticsearch([es_host], request_timeout=30)
        except Exception as e:
            raise Exception(f"Elasticsearch connection failed: {str(e)}")
    
    def get_today_ist_range(self):
        ist_tz = pytz.timezone('Asia/Kolkata')
        current_time_ist = datetime.now(ist_tz)
        today_midnight_ist = current_time_ist.replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_timestamp = int(today_midnight_ist.timestamp() * 1000)
        end_timestamp = int(current_time_ist.timestamp() * 1000)
        
        return start_timestamp, end_timestamp, today_midnight_ist, current_time_ist
    
    def get_custom_datetime_range(self, start_date_str, start_time_str=None, 
                                end_date_str=None, end_time_str=None):
        try:
            ist_tz = pytz.timezone('Asia/Kolkata')
            
            # Parse start datetime
            if start_time_str:
                dt_str = f"{start_date_str} {start_time_str}"
                start_dt_naive = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            else:
                start_dt_naive = datetime.strptime(start_date_str, '%Y-%m-%d')
            start_dt = ist_tz.localize(start_dt_naive)
            
            if end_date_str:
                if end_time_str:
                    dt_str = f"{end_date_str} {end_time_str}"
                    end_dt_naive = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
                else:
                    end_dt_naive = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_dt = ist_tz.localize(end_dt_naive)
            else:
                end_dt = start_dt
            
            # Convert to UTC timestamps
            start_time = int(start_dt.timestamp() * 1000)
            end_time = int(end_dt.timestamp() * 1000)
            print("start time:",start_time)
            print("end time:",end_time)
            return start_time, end_time, start_dt, end_dt
            
        except ValueError as e:
            raise ValueError(f"Invalid date/time format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS. Error: {str(e)}")
    
    def execute_es_query(self, start_time, end_time):
        es = self.get_es_client()
        
        query = {
            "size": 0,
            "aggs": {
                "sources": {
                    "terms": {"field": "articleSource", "size": 1000},
                    "aggs": {
                        "count_in_range": {
                            "filter": {
                                "range": {
                                    "articleInsertedDate": {"gt": start_time, "lt": end_time}
                                }
                            }
                        }
                    }
                }
            }
        }
        
        response = es.search(index="_all", body=query)
        return response
    
    def process_results(self, response, start_time, end_time):
        buckets = response['aggregations']['sources']['buckets']
        
        monitoring_data = []
        for bucket in buckets:
            monitoring_data.append({
                'source': bucket['key'],
                'total_docs': bucket['doc_count'],
                'docs_in_range': bucket['count_in_range']['doc_count'],
                'is_active': bucket['count_in_range']['doc_count'] > 0
            })
        
        monitoring_data.sort(key=lambda x: x['docs_in_range'], reverse=True)
        return monitoring_data
    
    def list(self, request):
        try:

            start_date_param = request.query_params.get('start_date')
            start_time_param = request.query_params.get('start_time')
            end_date_param = request.query_params.get('end_date')
            end_time_param = request.query_params.get('end_time')
            
            if start_date_param:
                start_time, end_time, start_dt, end_dt = self.get_custom_datetime_range(
                    start_date_param, start_time_param, end_date_param, end_time_param
                )
                date_type = "custom"
            else:
                start_time, end_time, start_dt, end_dt = self.get_today_ist_range()
                date_type = "today"
            
            response = self.execute_es_query(start_time, end_time)
            monitoring_data = self.process_results(response, start_time, end_time)
            
            return Response({
                'date_type': date_type,
                'timestamp': datetime.now().isoformat(),
                'time_range': {
                    'start': start_time,
                    'end': end_time,
                    'start_formatted': start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_formatted': end_dt.strftime('%Y-%m-%d %H:%M:%S'),
                },
                'data': monitoring_data,
                'total_sources': len(monitoring_data),
                'active_sources': sum(1 for item in monitoring_data if item['is_active'])
            })
            
        except ValueError as e:
            return Response({'error': str(e), 'message': 'Invalid date/time parameter'}, status=400)
        except Exception as e:
            return Response({'error': str(e), 'message': 'Failed to fetch monitoring data'}, status=500)