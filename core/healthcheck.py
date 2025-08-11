from django.http import JsonResponse
from elasticsearch import Elasticsearch
from django.conf import settings

def elasticsearch_healthcheck(request):
    # Get Elasticsearch host from settings
    es_config = getattr(settings, 'ELASTICSEARCH_DSL', {}).get('default', {})
    hosts = es_config.get('hosts', 'http://localhost:9200')
    
    # Ensure hosts is a list for Elasticsearch client
    if isinstance(hosts, str):
        hosts = [f"http://{hosts}"]
    elif isinstance(hosts, list):
        hosts = [f"http://{host}" if not host.startswith('http') else host for host in hosts]
    
    try:
        client = Elasticsearch(hosts)
        if client.ping():
            return JsonResponse({"status": "ok"})
        return JsonResponse({"status": "error", "message": "Elasticsearch not reachable"}, status=500)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
