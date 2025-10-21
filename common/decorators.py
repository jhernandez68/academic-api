from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from subjects.services import can_enroll
def validate_prerequisites(fn):
    @wraps(fn)
    def wrapper(view, request, *args, **kwargs):
        subject_id = request.data.get("subject_id")
        ok, msg = can_enroll(request.user, subject_id)
        if not ok:
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
        return fn(view, request, *args, **kwargs)
    return wrapper
