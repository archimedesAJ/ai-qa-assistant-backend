from django.urls import path
from .views import (
    GenerateTestCasesFromPrompt,
    GenerateTestCasesFromDocument,
    GenerateTestPlanFromPrompt,
    GenerateTestPlanFromDocument,
    TeamViewSet
)

urlpatterns = [
    path("generate/testcases/prompt/", GenerateTestCasesFromPrompt.as_view()),
    path("generate/testcases/document/", GenerateTestCasesFromDocument.as_view()),
    path("generate/testplan/prompt/", GenerateTestPlanFromPrompt.as_view()),
    path("generate/testplan/document/", GenerateTestPlanFromDocument.as_view()),
    path("teams/", TeamViewSet.as_view({'get': 'list'})),
]