import time, logging
from django.utils.deprecation import MiddlewareMixin
logger = logging.getLogger(__name__)
class RequestMetricsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()
    def process_response(self, request, response):
        try:
            duration = time.time() - getattr(request, "_start_time", time.time())
            user = getattr(request, "user", None)
            uid = user.id if getattr(user, "is_authenticated", False) else None
            logger.info(f"path={request.path} method={request.method} user={uid} duration_ms={int(duration*1000)}")
        except Exception:
            pass
        return response
