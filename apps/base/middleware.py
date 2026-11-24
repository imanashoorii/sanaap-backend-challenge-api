from django.db import connection
from django.http import JsonResponse
from django.core.cache import cache


class HealthCheckMiddleware:
    """
    This middleware checks the health status of the server (Readiness Probe)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/health/live/":
            return JsonResponse({"status": "alive"}, status=200)

        if request.path == "/health/ready/":
            try:
                connection.ensure_connection()
                cache.set("healthcheck_redis", "ok", timeout=5)
                if cache.get("healthcheck_redis") != "ok":
                    raise Exception("Redis error")
                return JsonResponse({"status": "ready"}, status=200)
            except Exception as e:
                return JsonResponse({"status": "unready", "error": str(e)}, status=503)

        return self.get_response(request)