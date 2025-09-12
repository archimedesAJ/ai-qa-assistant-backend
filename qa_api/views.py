from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .serializers import PromptSerializer, DocumentSerializer
from .parsing import extract_text_from_upload
from .prompts import build_requirement_text, test_case_prompt, test_plan_prompt
from ai_core.factory import get_provider
import json

def _assemble_context(validated):
    # app_context may be given by user; otherwise you can prefill defaults per project
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

        provider = get_provider()  # default provider per settings
        try:
            raw = provider.generate_test_cases(prompt, meta={"type": "test_cases"})
            # try to parse JSON if provider returned JSON
            try:
                parsed = json.loads(raw)
                return Response(parsed)
            except Exception:
                # return raw string in a consistent wrapper
                return Response({"raw": raw})
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
        # optional section hint combined at top
        section_hint = s.validated_data.get("section_hint", "")
        requirement_text = build_requirement_text("", "", "", (section_hint + "\n\n" + doc_text) if section_hint else doc_text, app_context)[:settings.MAX_CONTEXT_CHARS]
        prompt = test_case_prompt(app_context, requirement_text, max_cases)
        provider = get_provider()
        try:
            raw = provider.generate_test_cases(prompt, meta={"type": "test_cases", "source": "document"})
            try:
                parsed = json.loads(raw)
                return Response(parsed)
            except Exception:
                return Response({"raw": raw})
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
            raw = provider.generate_test_plan(prompt, meta={"type": "test_plan"})
            try:
                parsed = json.loads(raw)
                return Response(parsed)
            except Exception:
                return Response({"raw": raw})
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
            raw = provider.generate_test_plan(prompt, meta={"type": "test_plan", "source": "document"})
            try:
                parsed = json.loads(raw)
                return Response(parsed)
            except Exception:
                return Response({"raw": raw})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
