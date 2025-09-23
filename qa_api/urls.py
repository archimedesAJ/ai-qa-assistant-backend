from django.urls import path
# from rest_framework.routers import DefautltRouter
from .views import (
    GenerateTestCasesFromPrompt,
    GenerateTestCasesFromDocument,
    GenerateTestPlanFromPrompt,
    GenerateTestPlanFromDocument,
    GenerateTestPlanFromConfluenceUrl,
    AutoPopulateUserStoryDataFromKey,
    QAAssistantAPIView,
    QAFeedbackAPIView,
    KnowledgeBaseViewSet,
    TeamViewSet
)

urlpatterns = [
    path("generate/testcases/prompt/", GenerateTestCasesFromPrompt.as_view()),
    path("generate/testcases/document/", GenerateTestCasesFromDocument.as_view()),
    path("generate/testplan/prompt/", GenerateTestPlanFromPrompt.as_view()),
    path("generate/testplan/document/", GenerateTestPlanFromDocument.as_view()),
    path("generate/testplan/confluence_url/", GenerateTestPlanFromConfluenceUrl.as_view()),
    path("autopopulate/userstory/", AutoPopulateUserStoryDataFromKey.as_view()),
    path("teams/", TeamViewSet.as_view({'get': 'list'})),
    path("qa-assistant/", QAAssistantAPIView.as_view()),
    path("qa-feedback/", QAFeedbackAPIView.as_view()),  # POST for feedback
    path("knowledgebase/", KnowledgeBaseViewSet.as_view({'get': 'list', 'post': 'create'})),

]