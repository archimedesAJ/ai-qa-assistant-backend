import requests
import json
import re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from typing import Dict, Any
from django.conf import settings

class ConfluenceService:
    def __init__(self):
        self.domain = settings.JIRA_DOMAIN 
        self.email = settings.JIRA_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.base_url = f"https://{self.domain}/wiki/api/v2"
        
    def extract_page_id(self, confluence_url: str) -> str:
        """Extract page ID from various Confluence URL formats"""
        
        # Pattern 1: /pages/123456/
        match = re.search(r'/pages/(\d+)/', confluence_url)
        if match:
            return match.group(1)
        
        # Pattern 2: pageId=123456
        parsed_url = urlparse(confluence_url)
        query_params = parse_qs(parsed_url.query)
        if 'pageId' in query_params:
            return query_params['pageId'][0]
        
        # Pattern 3: /display/SPACE/Page+Title (needs resolution)
        match = re.search(r'/display/([^/]+)/(.+)', confluence_url)
        if match:
            space_key = match.group(1)
            page_title = match.group(2).replace('+', ' ')
            return self._resolve_page_by_title(space_key, page_title)
        
        raise ValueError('Unable to extract page ID from URL')
    
    def _resolve_page_by_title(self, space_key: str, page_title: str) -> str:
        """Resolve page ID from space key and title"""
        url = f"{self.base_url}/pages"
        params = {
            'space-key': space_key,
            'title': page_title,
            'limit': 1
        }
        
        response = requests.get(
            url,
            params=params,
            auth=(self.email, self.api_token),
            headers={'Accept': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                return data['results'][0]['id']
        
        raise ValueError(f'Page not found: {page_title} in space {space_key}')
    
    def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """Fetch page content from Confluence"""
        url = f"{self.base_url}/pages/{page_id}"
        params = {
            'body-format': 'atlas_doc_format', 'storage': 'true', 'expand': 'body.atlas_doc_format,body.storage,version,space'
        }

        response = requests.get(
            url,
            params=params,
            auth=(self.email, self.api_token),
            headers={'Accept': 'application/json'}
        )

        print("Confluence API response status:", response, response.text)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise ValueError('Page not found')
        elif response.status_code == 401:
            raise ValueError('Authentication failed')
        else:
            raise Exception(f'API request failed: {response.status_code}')
    
    def process_content(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean Confluence content"""
        title = page_data.get('title', '')
        
        # Try different body formats
        body_content = ''
        if 'body' in page_data:
            if 'atlas_doc_format' in page_data['body']:
                body_content = self._extract_from_atlas_format(
                    page_data['body']['atlas_doc_format']['value']
                )
                print("This is the body content", body_content)
            elif 'storage' in page_data['body']:
                body_content = self._extract_from_storage_format(
                    page_data['body']['storage']['value']
                )
                
        
        return {
            'title': title,
            'content': body_content,
            'page_id': page_data.get('id', ''),
            'space_id': page_data.get('spaceId', ''),
            'last_modified': page_data.get('version', {}).get('createdAt', ''),
            'url': f"https://{self.domain}/wiki/pages/viewpage.action?pageId={page_data.get('id', '')}"
        }
    
    def _extract_from_atlas_format(self, content: str) -> str:
        """Extract text from Atlas document format (JSON)"""
        try:
            doc = json.loads(content)
            return self._extract_text_from_nodes(doc.get('content', []))
        except json.JSONDecodeError:
            return content
    
    def _extract_text_from_nodes(self, nodes: list) -> str:
        """Recursively extract text from Atlas format nodes"""
        text = ''
        for node in nodes:
            if node.get('type') == 'text':
                text += node.get('text', '')
            elif 'content' in node:
                text += self._extract_text_from_nodes(node['content'])
            
            # Add line breaks for paragraph nodes
            if node.get('type') in ['paragraph', 'heading']:
                text += '\n\n'
        
        return text.strip()
    
    def _extract_from_storage_format(self, content: str) -> str:
        """Extract text from storage format (HTML/XHTML)"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean up whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def get_page_by_url(self, confluence_url: str) -> Dict[str, Any]:
        """Main method to get and process page content by URL"""
        # Extract page ID
        page_id = self.extract_page_id(confluence_url)
        print("This is the page id", page_id)

        # Fetch page data

        page_data = self.get_page_content(page_id)
        print("This is the page data", page_data)
        # Process and return content
        return self.process_content(page_data)