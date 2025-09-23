import requests
from typing import Dict, Any, List
from requests.auth import HTTPBasicAuth
from django.conf import settings

class JiraService:
    def __init__(self):
        self.domain = settings.JIRA_DOMAIN 
        self.email = settings.JIRA_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.base_url = f"https://{self.domain}/rest/api/3"
        
        #Specific fields we want to retrieve
        self.required_fields = [
            'summary',
            'description',
            'customfield_11332',  # Example custom field (Story Points)
        ]
    
    def get_story_by_key(self, story_key: str) -> Dict[str, Any]:
        """Get user story by key (e.g., 'HSP-123')"""
        url = f"{self.base_url}/issue/{story_key}"
        print("Fetching story from URL:", url)
        
        # Get all fields to identify custom fields
        params = {
            'fields': ','.join(self.required_fields)  # Fetch only required fields
        }

        print("What are these values 1", self.email)
        print("What are these values 2", self.api_token)
        print("Using params:", params)

        response = requests.get(
            url,
            params=params,
            auth=HTTPBasicAuth(self.email, self.api_token),
            headers={'Accept': 'application/json'}
        )

        print(response)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise ValueError(f'User story {story_key} not found')
        elif response.status_code == 401:
            raise ValueError('Authentication failed - check your Jira credentials')
        else:
            raise Exception(f'Jira API request failed: {response.status_code} - {response.text}')
    
    def get_stories_by_keys(self, story_keys: List[str]) -> List[Dict[str, Any]]:
        """Get multiple user stories by keys"""
        if not story_keys:
            return []
        
        # Use JQL to get multiple issues
        jql = f"key in ({','.join(story_keys)})"
        url = f"{self.base_url}/search"
        
        params = {
            'jql': jql,
            'fields': ','.join(self.required_fields),
            'maxResults': len(story_keys)
        }

        response = requests.get(
            url,
            params=params,
            auth=(self.email, self.api_token),
            headers={'Accept': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('issues', [])
        else:
            raise Exception(f'Jira API request failed: {response.status_code} - {response.text}')
    
    def get_available_fields(self) -> List[Dict[str, Any]]:
        """Get all available fields in Jira to help identify custom fields"""
        url = f"{self.base_url}/field"
        
        response = requests.get(
            url,
            auth=(self.email, self.api_token),
            headers={'Accept': 'application/json'}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return []