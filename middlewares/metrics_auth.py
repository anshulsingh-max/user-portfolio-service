import base64
from django.conf import settings
from django.http import HttpResponse

def basic_auth_required(get_response):
    """
    Wrap a view and protect it with Basic Auth.
    Reads METRICS_AUTH_USER / METRICS_AUTH_PASS from settings.
    """
    def _wrapped(request, *args, **kwargs):
        # Only protect when metrics are enabled
        if not getattr(settings, "ENABLE_METRICS", False) and not getattr(settings, "PROMETHEUS_METRICS_USERNAME", ''):
            return get_response(request, *args, **kwargs)

        auth = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth.startswith("Basic "):
            return _unauthorized()

        try:
            encoded = auth.split(" ", 1)[1].strip()
            username, password = base64.b64decode(encoded).decode("utf-8").split(":", 1)
        except Exception:
            return _unauthorized()

        if (
            username != getattr(settings, "PROMETHEUS_METRICS_USERNAME", "")
            or password != getattr(settings, "PROMETHEUS_METRICS_PASSWORD", "")
        ):
            return _unauthorized()

        return get_response(request, *args, **kwargs)

    return _wrapped

def _unauthorized():
    resp = HttpResponse("Unauthorized", status=401)
    resp["WWW-Authenticate"] = 'Basic realm="metrics"'
    return resp
