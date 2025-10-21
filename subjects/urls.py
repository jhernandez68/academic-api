from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet, StudentViewSet, InstructorViewSet
router = DefaultRouter()
router.register(r"", SubjectViewSet, basename="subjects")
router.register(r"student", StudentViewSet, basename="student")
router.register(r"instructor", InstructorViewSet, basename="instructor")
urlpatterns = router.urls
