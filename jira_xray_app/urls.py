from django.urls import path
from .views import TestCasesAPIView

urlpatterns = [
    path("testcases/<str:project_key>/", TestCasesAPIView.as_view(), name="fetch_test_cases")
]

