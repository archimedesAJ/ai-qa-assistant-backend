from abc import ABC, abstractmethod
from typing import Any,  Dict

class BaseLLMProvider(ABC):

    """
    Minimal provider interface.
    Implementations should return structured strings (JSON) or Python dicts.
    """

    @abstractmethod
    def generate_test_cases(self, prompt: str, meta: Dict[str, Any] = None) -> str:
        pass


    @abstractmethod
    def generate_test_plan(self, prompt: str, meta: Dict[str, Any] = None ) -> str:
        pass


    
