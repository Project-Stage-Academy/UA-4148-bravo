from django.http import JsonResponse
from elasticsearch import Elasticsearch

def elasticsearch_healthcheck(request):
    client = Elasticsearch("http://localhost:9200")
    if client.ping():
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=500)
