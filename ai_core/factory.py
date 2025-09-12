from django.conf import settings
from .openapi_provider import OpenAIProvider
# future imports: from .anthropic_provider import AnthropicProvider

def get_provider():
    provider_name = getattr(settings, "AI_PROVIDER", "mock")
    if provider_name == "openai":
        return OpenAIProvider()
    # elif provider_name == "anthropic":
    #     return AnthropicProvider()

    elif provider_name == 'mock':
        from .mock_provider import MockProvider
        return MockProvider();

    raise ValueError(f"Unsupported provider: {provider_name}")
