from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.conf import settings
from .models import Team
from .serializers import TeamSerializer, PromptSerializer, DocumentSerializer
from .parsing import extract_text_from_upload
from .prompts import build_requirement_text, test_case_prompt, test_plan_prompt
from ai_core.factory import get_provider
import json


def _assemble_context(validated):
    """
    Resolve app_context from team if provided, else fallback to user input,
    else default to generic context.
    """
    team_id = validated.get("team_id")
    if team_id:
        try:
            team = Team.objects.get(id=team_id)
            return team.description or "Generic QA context"
        except Team.DoesNotExist:
            pass
    return validated.get("app_context", "") or "Generic web/mobile application for feature-level QA."


class GenerateTestCasesFromPrompt(APIView):
    def post(self, request):
        s = PromptSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        user_story = s.validated_data.get("user_story", "")
        ac = s.validated_data.get("acceptance_criteria", "")
        feature_description = s.validated_data.get("feature_description", "")
        app_context = _assemble_context(s.validated_data)
        max_cases = s.validated_data.get("max_cases", 8)

        requirement_text = build_requirement_text(user_story, ac, feature_description, "", app_context)
        prompt = test_case_prompt(app_context, requirement_text, max_cases)

        provider = get_provider()
        try:
            result = provider.generate(prompt, meta={"type": "test_cases"})
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class GenerateTestCasesFromDocument(APIView):
    def post(self, request):
        s = DocumentSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        f = s.validated_data["document"]
        doc_text = extract_text_from_upload(f)
        if not doc_text.strip():
            return Response({"detail": "Could not extract text from document."}, status=400)

        app_context = _assemble_context(s.validated_data)
        max_cases = s.validated_data.get("max_cases", 8)
        section_hint = s.validated_data.get("section_hint", "")

        requirement_text = build_requirement_text(
            "", "", "", (section_hint + "\n\n" + doc_text) if section_hint else doc_text, app_context
        )[:settings.MAX_CONTEXT_CHARS]

        prompt = test_case_prompt(app_context, requirement_text, max_cases)

        provider = get_provider()
        try:
            result = provider.generate(prompt, meta={"type": "test_cases", "source": "document"})
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class GenerateTestPlanFromPrompt(APIView):
    def post(self, request):
        s = PromptSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        user_story = s.validated_data.get("user_story", "")
        ac = s.validated_data.get("acceptance_criteria", "")
        feature_description = s.validated_data.get("feature_description", "")
        app_context = _assemble_context(s.validated_data)

        requirement_text = build_requirement_text(user_story, ac, feature_description, "", app_context)
        prompt = test_plan_prompt(app_context, requirement_text)

        provider = get_provider()
        try:
            result = provider.generate(prompt, meta={"type": "test_plan"})
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class GenerateTestPlanFromDocument(APIView):
    def post(self, request):
        s = DocumentSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        f = s.validated_data["document"]
        doc_text = extract_text_from_upload(f)
        if not doc_text.strip():
            return Response({"detail": "Could not extract text from document."}, status=400)

        app_context = _assemble_context(s.validated_data)

        requirement_text = build_requirement_text("", "", "", doc_text, app_context)[:settings.MAX_CONTEXT_CHARS]
        prompt = test_plan_prompt(app_context, requirement_text)

        provider = get_provider()
        try:
            result = provider.generate(prompt, meta={"type": "test_plan", "source": "document"})
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)


class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer