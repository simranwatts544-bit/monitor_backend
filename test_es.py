from elasticsearch import Elasticsearch

# Test connection
es = Elasticsearch(['http://142.198.63.54:9200'], request_timeout=30)

try:
    info = es.info()
    print("Elasticsearch connected successfully!")
    print(f"Version: {info['version']['number']}")
except Exception as e:
    print(f"Connection failed: {e}")