from rest_framework import serializers

class PromptSerializer(serializers.Serializer):
    user_story = serializers.CharField(required=False, allow_blank=True)
    acceptance_criteria = serializers.CharField(required=False, allow_blank=True)
    feature_description = serializers.CharField(required=False, allow_blank=True)
    app_context = serializers.CharField(required=False, allow_blank=True)
    max_cases = serializers.IntegerField(required=False, default=8, min_value=1, max_value=50)

class DocumentSerializer(serializers.Serializer):
    document = serializers.FileField()
    app_context = serializers.CharField(required=False, allow_blank=True)
    section_hint = serializers.CharField(required=False, allow_blank=True)
    max_cases = serializers.IntegerField(required=False, default=8, min_value=1, max_value=50)
