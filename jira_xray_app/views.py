from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from requests.auth import HTTPBasicAuth
from django.conf import settings

class TestCasesAPIView(APIView):
    def __init__(self):
        super().__init__()
        self.jira_url = settings.JIRA_BASE_URL
        self.auth = HTTPBasicAuth(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)
    
    def get(self, request, project_key):
        """
        GET /api/test-cases/{project_key}/
        """
        try:
            # Build JQL query
            jql = f'project = "{project_key}" AND issuetype = "Test"'
            
            # Add additional filters if provided
            status_filter = request.query_params.get('status')
            if status_filter:
                jql += f' AND status = "{status_filter}"'
            
            assignee_filter = request.query_params.get('assignee')
            if assignee_filter:
                jql += f' AND assignee = "{assignee_filter}"'
            
            # Pagination
            start_at = int(request.query_params.get('start_at', 0))
            max_results = int(request.query_params.get('max_results', 50))
            
            url = f"{self.jira_url}/rest/api/3/search"
            params = {
                'jql': jql,
                'startAt': start_at,
                'maxResults': max_results,
                'fields': 'summary,description,status,priority,assignee,labels,created,updated'
            }
            
            response = requests.get(url, auth=self.auth, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Transform the data if needed
                transformed_issues = []
                for issue in data['issues']:
                    transformed_issue = {
                        'key': issue['key'],
                        'summary': issue['fields']['summary'],
                        'description': issue['fields'].get('description', ''),
                        'status': issue['fields']['status']['name'],
                        'priority': issue['fields']['priority']['name'] if issue['fields']['priority'] else None,
                        'assignee': issue['fields']['assignee']['displayName'] if issue['fields']['assignee'] else None,
                        'labels': issue['fields']['labels'],
                        'created': issue['fields']['created'],
                        'updated': issue['fields']['updated']
                    }
                    transformed_issues.append(transformed_issue)
                
                return Response({
                    'total': data['total'],
                    'start_at': data['startAt'],
                    'max_results': data['maxResults'],
                    'issues': transformed_issues
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    'error': f'Failed to fetch data from Jira: {response.status_code}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)