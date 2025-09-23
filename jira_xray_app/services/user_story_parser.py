import re
from typing import Dict, Any, Optional, List


class StoryParser:

    def parse_issue(self, jira_issue: dict) -> dict:
        """Parse a Jira issue into structured story data."""
        fields = jira_issue.get("fields", {})

        summary = fields.get("summary", "")
        description = self._extract_text_from_adf(fields.get("description", {}))
        acceptance_criteria = self._extract_text_from_adf(fields.get("customfield_11332", {}))

        return {
            "id": jira_issue.get("id", ""),
            "key": jira_issue.get("key", ""),
            "summary": summary,
            "description": description,
            "acceptance_criteria": acceptance_criteria,
        }

    def _extract_text_from_adf(self, adf_content: dict) -> str:
        """Extract plain text from Atlassian Document Format (ADF)."""
        if not adf_content:
            return ""

        def extract(nodes):
            text_parts = []
            for node in nodes:
                if node.get("type") == "text":
                    text_parts.append(node.get("text", ""))
                elif node.get("type") == "hardBreak":
                    text_parts.append("\n")
                elif "content" in node:
                    text_parts.append(extract(node["content"]))
            return "".join(text_parts)

        if isinstance(adf_content, dict) and "content" in adf_content:
            return extract(adf_content["content"]).strip()
        return str(adf_content)