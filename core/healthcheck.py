from django.http import JsonResponse
from elasticsearch import Elasticsearch, ConnectionError

def elasticsearch_healthcheck(request):
    es = Elasticsearch("http://localhost:9200")
    try:
        if es.ping():
            return JsonResponse({'elasticsearch': 'ok'})
        else:
            return JsonResponse({'elasticsearch': 'unreachable'}, status=503)
    except ConnectionError:
        return JsonResponse({'elasticsearch': 'error'}, status=500)
