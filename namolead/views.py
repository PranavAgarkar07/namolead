from django.db import connection
from django.http import JsonResponse


def health(request):
    try:
        connection.ensure_connection()
        database = "ok"
        status = "ok"
        http_status = 200
    except Exception:
        database = "error"
        status = "degraded"
        http_status = 503
    return JsonResponse({"status": status, "database": database}, status=http_status)
