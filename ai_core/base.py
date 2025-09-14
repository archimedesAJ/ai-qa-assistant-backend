# ai_core/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseLLMProvider(ABC):
    """
    Minimal provider interface.
    All providers should implement a single entrypoint.
    Must return a structured dict containing test_cases, test_plan, and raw.
    """

    @abstractmethod
    def generate(self, prompt: str, meta: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate test artifacts from a prompt.
        Should return a dict like:
        {
            "test_cases": [...],
            "test_plan": {...},
            "raw": "original unparsed text"
        }
        """
        pass
