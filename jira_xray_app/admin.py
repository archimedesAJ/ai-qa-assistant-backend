from django.contrib import admin
from qa_api.models import Team, KnowledgeBase, QAQuery, FAQ    # replace with your model

admin.site.register(Team)
admin.site.register(KnowledgeBase)
admin.site.register(QAQuery)
admin.site.register(FAQ)
