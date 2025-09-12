import os
import json
from typing import Any, Dict
from openai import OpenAI
from django.conf import settings
from .base import BaseLLMProvider

class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=api_key)
        self.model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    def _call(self, prompt: str, temperature: float = 0.2) -> str:
        """
        Use Responses API if available, fallback to chat completions style.
        Return text content.
        """
        try:
            # Responses API style
            resp = self.client.responses.create(
                model=self.model,
                input=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            # Many SDKs provide .output_text; handle robustly:
            if hasattr(resp, "output_text"):
                return resp.output_text
            # fallback
            text = ""
            if hasattr(resp, "output"):
                # combine text content
                for item in resp.output:
                    if "content" in item and isinstance(item["content"], list):
                        for c in item["content"]:
                            if c.get("type") == "output_text":
                                text += c.get("text", "")
            if text:
                return text
            # last resort: str()
            return str(resp)
        except Exception:
            # fallback to chat completions path (older SDK style)
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            # attempt to extract message content
            try:
                return resp.choices[0].message.content
            except Exception:
                return str(resp)

    def generate_test_cases(self, prompt: str, meta: Dict[str, Any] = None) -> str:
        return self._call(prompt, temperature=0.2)

    def generate_test_plan(self, prompt: str, meta: Dict[str, Any] = None) -> str:
        return self._call(prompt, temperature=0.1)
