from rest_framework import serializers
from .models import Team, FAQ, KnowledgeBase, QAQuery

class PromptSerializer(serializers.Serializer):
    user_story = serializers.CharField(required=False, allow_blank=True)
    acceptance_criteria = serializers.CharField(required=False, allow_blank=True)
    feature_description = serializers.CharField(required=False, allow_blank=True)
    app_context = serializers.CharField(required=False, allow_blank=True)
    team_id = serializers.IntegerField(required=True)
    max_cases = serializers.IntegerField(required=False, default=8, min_value=1, max_value=50)

class DocumentSerializer(serializers.Serializer):
    # Accept multiple files (BRD, SRS, etc.)
    documents = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False
    )
    app_context = serializers.CharField(required=False, allow_blank=True)
    section_hint = serializers.CharField(required=False, allow_blank=True)
    team_id = serializers.IntegerField(required=True)
    max_cases = serializers.IntegerField(required=False, default=8, min_value=1, max_value=50)

class ConfluencePageSerializer(serializers.Serializer):
    confluence_url = serializers.URLField(required=True)
    app_context = serializers.CharField(required=False, allow_blank=True)
    team_id = serializers.IntegerField(required=True)


class UserStorySerializer(serializers.Serializer):
    story_key = serializers.CharField(required=True, help_text="Jira story key, e.g., 'HSP-123'")


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name", "description", "context_info", "tech_stack", "key_contacts", 
                  "created_at", "updated_at"]


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    project_team = TeamSerializer(read_only=True)
    project_team_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = KnowledgeBase
        fields = ['id', 'title', 'content', 'category', 'project_team', 'project_team_id', 
                 'tags', 'created_by', 'last_updated', 'usage_count']

class QAQuerySerializer(serializers.ModelSerializer):
    project_team = TeamSerializer(read_only=True)
    
    class Meta:
        model = QAQuery
        fields = ['id', 'question', 'response', 'user_feedback', 'project_team', 
                 'response_time', 'created_at']

class QAQueryCreateSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000)
    project_team_id = serializers.IntegerField(required=False, allow_null=True)
    user_context = serializers.JSONField(required=False, default=dict)

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'category', 'project_team', 'frequency']

class FeedbackSerializer(serializers.Serializer):
    query_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comments = serializers.CharField(required=False)