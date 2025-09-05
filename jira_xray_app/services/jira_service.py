import requests
from django.conf import settings

def get_test_cases(project_key, token, start=0, max_results=100):
    url = f"{settings.JIRA_BASE_URL}/rest/api/3/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    jql = f'project = "{project_key}" AND issuetype = Test'

    payload = {
        "jql": jql,
        "startAt": start,
        "maxResults": max_results,
        "fields": ["summary", "key", "status"]
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()