from django.http import JsonResponse
from elasticsearch import Elasticsearch
from django.conf import settings


def elasticsearch_healthcheck(request):
    """
    Performs a health check to verify connectivity with the Elasticsearch cluster.

    The function:
    - Retrieves Elasticsearch hosts from the Django settings (ELASTICSEARCH_DSL).
    - Normalizes the hosts to a list of strings.
    - Adds the "http://" scheme to hosts that lack a scheme.
    - Pings the Elasticsearch cluster to check if it is reachable.
    - Returns a JSON response indicating the health status.

    Returns:
        JsonResponse:
            - {"status": "ok"} if Elasticsearch is reachable.
            - {"status": "error", "message": "..."} if Elasticsearch is unreachable or any error occurs.
            - HTTP 400 if no valid hosts are configured.
    """
    es_config = getattr(settings, 'ELASTICSEARCH_DSL', {}).get('default', {})
    hosts = es_config.get('hosts', 'http://localhost:9200')

    hosts = hosts if isinstance(hosts, list) else [hosts]

    valid_hosts = []
    for h in hosts:
        h = str(h).strip()
        if not h:
            continue
        if not h.startswith(('http://', 'https://')):
            h = f"http://{h}"
        if h.startswith(('http://', 'https://')):
            valid_hosts.append(h)

    if not valid_hosts:
        return JsonResponse({"status": "error", "message": "No valid Elasticsearch hosts configured"}, status=400)

    try:
        client = Elasticsearch(valid_hosts)
        if client.ping():
            return JsonResponse({"status": "ok"})
        return JsonResponse({"status": "error", "message": "Elasticsearch not reachable"}, status=500)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
