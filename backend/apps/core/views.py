from django.http import JsonResponse


def health_check(request):
    """Liveness/readiness probe for Render (and anyone else polling us)."""
    return JsonResponse({"status": "ok"})
