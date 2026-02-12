import time
from datetime import datetime, timedelta
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from elasticsearch import Elasticsearch
from django.conf import settings
import pytz

class MonitoringViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_es_client(self):
        """Get Elasticsearch client - compatible with newer versions"""
        try:
            es_host = getattr(settings, 'ELASTICSEARCH_HOST', 'http://142.198.63.54:9200')
            return Elasticsearch([es_host], request_timeout=30)
        except Exception as e:
            raise Exception(f"Elasticsearch connection failed: {str(e)}")
    
    def get_today_midnight_to_now_range(self):
        """Get timestamp range from 12 AM today (IST) to current time (IST)"""
        # Get current time in IST timezone
        ist_tz = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist_tz)
        
        # Get midnight (12 AM) of today in IST
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Convert to UTC timestamps (for Elasticsearch)
        start_time = int(midnight.timestamp() * 1000)
        end_time = int(now.timestamp() * 1000)
        
        return start_time, end_time, midnight, now
    
    def get_custom_date_range(self, start_date_str, end_date_str=None):
        """Get timestamp range for custom dates (interpreted as IST)"""
        try:
            ist_tz = pytz.timezone('Asia/Kolkata')
            
            # Parse start date and make it timezone-aware (IST midnight)
            start_date_naive = datetime.strptime(start_date_str, '%Y-%m-%d')
            start_date = ist_tz.localize(start_date_naive)
            
            if end_date_str:
                # Parse end date and make it timezone-aware (IST end of day)
                end_date_naive = datetime.strptime(end_date_str, '%Y-%m-%d')
                end_date = ist_tz.localize(end_date_naive)
                # Set to end of day
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                # If no end date, use end of start date
                end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Convert to UTC timestamps (for Elasticsearch)
            start_time = int(start_date.timestamp() * 1000)
            end_time = int(end_date.timestamp() * 1000)
            
            return start_time, end_time, start_date, end_date
            
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD. Error: {str(e)}")
    
    def execute_es_query(self, start_time, end_time):
        """Execute Elasticsearch query with given time range"""
        es = self.get_es_client()
        
        query = {
            "size": 0,
            "aggs": {
                "sources": {
                    "terms": {
                        "field": "articleSource",
                        "size": 1000
                    },
                    "aggs": {
                        "count_in_range": {
                            "filter": {
                                "range": {
                                    "articleInsertedDate": {
                                        "gt": start_time,
                                        "lt": end_time
                                    }
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
        """Process Elasticsearch results into formatted data"""
        buckets = response['aggregations']['sources']['buckets']
        
        monitoring_data = []
        for bucket in buckets:
            monitoring_data.append({
                'source': bucket['key'],
                'total_docs': bucket['doc_count'],
                'docs_in_range': bucket['count_in_range']['doc_count'],
                'is_active': bucket['count_in_range']['doc_count'] > 0
            })
        
        # Sort by docs_in_range (descending)
        monitoring_data.sort(key=lambda x: x['docs_in_range'], reverse=True)
        
        return monitoring_data
    
    def list(self, request):
        """
        Default endpoint: Today's data (12 AM to now in IST)
        Query parameters:
        - start_date: YYYY-MM-DD (optional)
        - end_date: YYYY-MM-DD (optional, defaults to start_date if not provided)
        """
        try:
            # Check for custom date parameters
            start_date_param = request.query_params.get('start_date')
            end_date_param = request.query_params.get('end_date')
            
            if start_date_param:
                # Custom date range
                start_time, end_time, start_dt, end_dt = self.get_custom_date_range(start_date_param, end_date_param)
                date_type = "custom"
            else:
                # Default: Today from 12 AM to now (IST)
                start_time, end_time, start_dt, end_dt = self.get_today_midnight_to_now_range()
                date_type = "today"
            
            # Execute query
            response = self.execute_es_query(start_time, end_time)
            
            # Process results
            monitoring_data = self.process_results(response, start_time, end_time)
            
            # Format time range info (already in IST timezone)
            return Response({
                'date_type': date_type,
                'timestamp': datetime.now().isoformat(),
                'time_range': {
                    'start': start_time,
                    'end': end_time,
                    'start_formatted': start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_formatted': end_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'start_date_only': start_dt.strftime('%Y-%m-%d'),
                    'end_date_only': end_dt.strftime('%Y-%m-%d')
                },
                'data': monitoring_data,
                'total_sources': len(monitoring_data),
                'active_sources': sum(1 for item in monitoring_data if item['is_active'])
            })
            
        except ValueError as e:
            return Response({
                'error': str(e),
                'message': 'Invalid date parameter'
            }, status=400)
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'Failed to fetch monitoring data'
            }, status=500)