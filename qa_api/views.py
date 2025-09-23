import time
from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.conf import settings
from .models import Team, KnowledgeBase, FAQ, QAQuery
from .serializers import QAQueryCreateSerializer, TeamSerializer, PromptSerializer, DocumentSerializer, ConfluencePageSerializer,UserStorySerializer, KnowledgeBaseSerializer, FeedbackSerializer
from .parsing import extract_text_from_upload
from .prompts import build_requirement_text, test_case_prompt, test_plan_prompt
from ai_core.factory import get_provider
import json
from rest_framework.decorators import action
from django.db.models import Q, Count, Avg


def _assemble_context(validated):
    """
    Resolve app_context from team if provided, else fallback to user input,
    else default to generic context.
    """
    team_id = validated.get("team_id")
    if team_id:
        try:
            team = Team.objects.get(id=team_id)
            return team.context_info or "Generic QA context"
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
        print("App context:", app_context)
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

        files = s.validated_data["documents"]

        # Extract text from each uploaded file
        doc_texts = []
        for f in files:
            text = extract_text_from_upload(f)
            if text.strip():
                doc_texts.append(text)

        if not doc_texts:
            return Response(
                {"detail": "Could not extract text from any document."},
                status=400
            )

        # Combine into one string (works for 1 file or many)
        combined_text = "\n\n".join(doc_texts)

        app_context = _assemble_context(s.validated_data)

        requirement_text = build_requirement_text("", "", "", combined_text, app_context)[:settings.MAX_CONTEXT_CHARS]
        prompt = test_plan_prompt(app_context, requirement_text)

        provider = get_provider()
        try:
            result = provider.generate(prompt, meta={"type": "test_plan", "source": "document"})
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        
class GenerateTestPlanFromConfluenceUrl(APIView):
    def post(self, request):
        s = ConfluencePageSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        confluence_url = s.validated_data.get("confluence_url", "")
        if not confluence_url:
            return Response({"detail": "Confluence URL is required."}, status=400)

        app_context = _assemble_context(s.validated_data)

        from confluence.services.confluence_services import ConfluenceService

        try:
            # Get page content
            confluence = ConfluenceService()
            page_content = confluence.get_page_by_url(confluence_url)

            # Validate that we have content
            if not page_content['content'].strip():
                return Response({"detail": "Confluence page has no content."}, status=400)
            doc_text = page_content['content']

            # print("The content extracted from Confluence is:", doc_text[:500])

            requirement_text = build_requirement_text("", "", "", doc_text, app_context)[:settings.MAX_CONTEXT_CHARS]
            prompt = test_plan_prompt(app_context, requirement_text)

            provider = get_provider()
            result = provider.generate(prompt, meta={"type": "test_plan", "source": "confluence"})
            return Response(result)
        
        except ValueError as ve:
            return Response({"detail": str(ve)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        

class AutoPopulateUserStoryDataFromKey(APIView):
    def post(self, request):
        s = UserStorySerializer(data=request.data)
        s.is_valid(raise_exception=True)

        story_key = s.validated_data.get("story_key", "").strip()
        if not story_key:
            return Response({"detail": "User story key is required."}, status=400)

        from jira_xray_app.services.jira_service import JiraService
        from jira_xray_app.services.user_story_parser import StoryParser

        try:
            jira = JiraService()
            parser = StoryParser()

            story_data = jira.get_story_by_key(story_key)
            print("Raw story:", story_data)

            parsed_story = parser.parse_issue(story_data)
            print("Parsed story:", parsed_story)

            return Response(parsed_story)

        except ValueError as ve:
            return Response({"detail": str(ve)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        

class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        project_id = self.request.query_params.get('project_id')
        
        if category:
            queryset = queryset.filter(category=category)
        if project_id:
            queryset = queryset.filter(
                Q(project_team_id=project_id) | Q(category='universal')
            )
        
        return queryset.order_by('-last_updated')
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search knowledge base by content"""
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
        
        results = self.queryset.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(tags__contains=[query])
        )
        
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

class QAAssistantAPIView(APIView):
    """Main API for QA Assistant interactions"""
    
    def post(self, request):
        serializer = QAQueryCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        start_time = time.time()
        question = serializer.validated_data['question']
        project_team_id = serializer.validated_data.get('project_team_id')
        user_context = serializer.validated_data.get('user_context', {})
        
        try:
            # Get relevant context
            context = self._get_relevant_context(question, project_team_id)
            
            # Generate AI response
            ai_response = self._generate_ai_response(question, context, project_team_id)
            
            # Get suggested follow-ups and related docs
            followups = self._get_suggested_followups(question, context)
            related_docs = self._get_related_documents(question, project_team_id)
            
            # Log the query
            query_obj = QAQuery.objects.create(
                question=question,
                response=ai_response,
                project_team_id=project_team_id,
                response_time=time.time() - start_time
            )
            
            return Response({
                'query_id': query_obj.id,
                'response': ai_response,
                'suggested_followups': followups,
                'related_docs': related_docs,
                'response_time': query_obj.response_time
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate response: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_relevant_context(self, question, project_team_id):
        """Retrieve relevant knowledge base entries"""
        # Universal knowledge
        universal_kb = KnowledgeBase.objects.filter(category='universal')
        
        # Project-specific knowledge
        project_kb = KnowledgeBase.objects.none()
        if project_team_id:
            project_kb = KnowledgeBase.objects.filter(project_team_id=project_team_id)
        
        # Search for relevant entries based on question keywords
        question_lower = question.lower()
        keywords = question_lower.split()
        
        relevant_universal = universal_kb.filter(
            Q(title__icontains=question_lower) |
            Q(content__icontains=question_lower) |
            Q(tags__overlap=keywords)
        )[:5]
        
        relevant_project = project_kb.filter(
            Q(title__icontains=question_lower) |
            Q(content__icontains=question_lower) |
            Q(tags__overlap=keywords)
        )[:5]
        
        return {
            'universal': KnowledgeBaseSerializer(relevant_universal, many=True).data,
            'project_specific': KnowledgeBaseSerializer(relevant_project, many=True).data
        }
    
    def _generate_ai_response(self, question, context, project_team_id):
        """Generate response using OpenAI API"""
        
        # Get project info
        project_info = ""
        if project_team_id:
            try:
                project = Team.objects.get(id=project_team_id)
                project_info = f"""
                Current Project: {project.name}
                Description: {project.description}
                Tech Stack: {', '.join(project.tech_stack)}
                Key Contacts: {', '.join(project.key_contacts)}
                """
            except Team.DoesNotExist:
                pass
        
        # Build context string
        context_str = ""
        if context['universal']:
            context_str += "Universal QA Standards:\n"
            for item in context['universal']:
                context_str += f"- {item['title']}: {item['content'][:200]}...\n"
        
        if context['project_specific']:
            context_str += "\nProject-Specific Knowledge:\n"
            for item in context['project_specific']:
                context_str += f"- {item['title']}: {item['content'][:200]}...\n"
        
        system_prompt = f"""
        You are a QA Knowledge Assistant for a software development organization with 7 project teams.
        
        {project_info}
        
        Available Knowledge:
        {context_str}
        
        Guidelines:
        - Provide specific, actionable answers based on available knowledge
        - If you don't have specific information, acknowledge it and suggest who to ask
        - Ask for project clarification if the answer depends on which project they're working on
        - Keep responses concise but complete (aim for 2-3 paragraphs max)
        - Include step-by-step instructions when appropriate
        - Reference relevant documentation from the knowledge base
        - Suggest escalation to team leads for complex project-specific issues
        
        Response Format:
        - Start with direct answer to the question
        - Provide specific steps or guidance
        - End with additional resources or next steps if relevant
        """
        
        # response = client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": question}
        #     ],
        #     temperature=0.3,
        #     max_tokens=500
        # )
        
        # return response.choices[0].message.content
        provider = get_provider()
        result = provider.chat_completion(system_prompt, question, temperature=0.3)
        return result
    
    def _get_suggested_followups(self, question, context):
        """Generate suggested follow-up questions"""
        common_followups = {
            'onboarding': [
                "What tools do I need access to?",
                "Who should I contact for help?",
                "What should I focus on in my first sprint?"
            ],
            'testing': [
                "What are common edge cases to test?",
                "How do I handle test data setup?",
                "What's our automation testing approach?"
            ],
            'procedures': [
                "What are the acceptance criteria?",
                "How do I escalate this issue?",
                "What's our definition of done?"
            ]
        }
        
        # Simple keyword matching for now
        question_lower = question.lower()
        if any(word in question_lower for word in ['new', 'onboard', 'start']):
            return common_followups['onboarding']
        elif any(word in question_lower for word in ['test', 'bug', 'case']):
            return common_followups['testing']
        else:
            return common_followups['procedures']
    
    def _get_related_documents(self, question, project_team_id):
        """Get related documentation"""
        # Find related KB articles
        related = KnowledgeBase.objects.filter(
            Q(title__icontains=question) | 
            Q(content__icontains=question)
        )
        
        if project_team_id:
            related = related.filter(
                Q(project_team_id=project_team_id) | Q(category='universal')
            )
        
        return KnowledgeBaseSerializer(related[:3], many=True).data
    

class QAFeedbackAPIView(APIView):
    """Handle user feedback on AI responses"""
    
    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query_id = serializer.validated_data['query_id']
        rating = serializer.validated_data['rating']
        comments = serializer.validated_data.get('comments', '')
        
        try:
            query = QAQuery.objects.get(id=query_id)
            query.user_feedback = rating
            query.save()
            
            # TODO: Store detailed feedback comments if needed
            
            return Response({'message': 'Feedback recorded successfully'})
        except QAQuery.DoesNotExist:
            return Response(
                {'error': 'Query not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        

class QAAnalyticsAPIView(APIView):
    """Analytics endpoint for QA assistant usage"""
    
    def get(self, request):
        # Basic analytics
        total_queries = QAQuery.objects.count()
        avg_rating = QAQuery.objects.filter(
            user_feedback__isnull=False
        ).aggregate(avg_rating=Avg('user_feedback'))['avg_rating']
        
        # Most common questions (by similarity would be complex, so using exact matches)
        common_questions = QAQuery.objects.values('question').annotate(
            count=Count('question')
        ).filter(count__gt=1).order_by('-count')[:10]
        
        # Knowledge base stats
        kb_stats = KnowledgeBase.objects.values('category').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_queries': total_queries,
            'average_rating': round(avg_rating or 0, 2),
            'common_questions': list(common_questions),
            'knowledge_base_stats': list(kb_stats),
            'total_kb_articles': KnowledgeBase.objects.count()
        })