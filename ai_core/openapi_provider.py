# ai_core/openai_provider.py
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
        """Internal wrapper for calling OpenAI and returning text."""
        try:
            resp = self.client.responses.create(
                model=self.model,
                input=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            if hasattr(resp, "output_text"):
                return resp.output_text
            text = ""
            if hasattr(resp, "output"):
                for item in resp.output:
                    if "content" in item and isinstance(item["content"], list):
                        for c in item["content"]:
                            if c.get("type") == "output_text":
                                text += c.get("text", "")
            return text or str(resp)
        except Exception:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            try:
                return resp.choices[0].message.content
            except Exception:
                return str(resp)

    def generate(self, prompt: str, meta: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Unified entrypoint for generating artifacts.
        Returns structured dict depending on meta["type"].
        """
        meta = meta or {}
        type_ = meta.get("type") 

        # Adjust temperature for variety
        temperature = 0.2 if type_ == "test_cases" else 0.1
        raw = self._call(prompt, temperature=temperature)

        # Wrap output in consistent dict
        if type_ == "test_cases":
            return {"test_cases": raw}
        elif type_ == "test_plan":
            return {"test_plan": raw}
        else:
            return {"raw": raw}
        
    def chat_completion(self, system_prompt: str, question: str, temperature: float = 0.3) -> str:
        """Call OpenAI Responses API and return a plain string"""
        try:
            resp = self.client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=temperature,
                max_tokens=500
            )
            if hasattr(resp, "output_text"):
                return resp.output_text
            text = ""
            if hasattr(resp, "output"):
                for item in resp.output:
                    if "content" in item and isinstance(item["content"], list):
                        for c in item["content"]:
                            if c.get("type") == "output_text":
                                text += c.get("text", "")
            return text or str(resp)
        except Exception as e:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=temperature,
            )
            try:
                return resp.choices[0].message.content
            except Exception:
                return str(resp)

