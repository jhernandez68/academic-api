from django.urls import path
from .views import StudentReportCSV, InstructorReportCSV
urlpatterns = [
    path("student/<int:id>/", StudentReportCSV.as_view()),
    path("instructor/<int:id>/", InstructorReportCSV.as_view()),
]
