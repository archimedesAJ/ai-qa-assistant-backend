from django.db import models

# Create your models here.

class Team(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    context_info = models.TextField()  # writeup about the application/project(s) under this team
    tech_stack = models.CharField(max_length=255, blank=True, null=True)  # e.g., "Django, React, PostgreSQL"
    key_contacts = models.CharField(max_length=255, blank=True, null=True)  # list of dicts with name, role, email

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    

class KnowledgeBase(models.Model):
    CATEGORY_CHOICES = [
        ('universal', 'Universal QA Standards'),
        ('project_specific', 'Project Specific'),
        ('onboarding', 'Onboarding'),
        ('troubleshooting', 'Troubleshooting'),
        ('tools', 'Tools & Systems'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    project_team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    tags = models.JSONField(default=list)
    created_by = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class QAQuery(models.Model):
    question = models.TextField()
    response = models.TextField()
    user_feedback = models.IntegerField(null=True, blank=True)  # 1-5 rating
    project_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    response_time = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)


class FAQ(models.Model):
    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(max_length=50)
    project_team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    frequency = models.IntegerField(default=0)