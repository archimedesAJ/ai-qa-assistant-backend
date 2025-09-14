from django.conf import settings
# future imports: from .anthropic_provider import AnthropicProvider

_provider_instance = None

def get_provider():
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider_name = getattr(settings, "AI_PROVIDER", "mock")
    if provider_name == "openai":
        from .openapi_provider import OpenAIProvider
        _provider_instance = OpenAIProvider()
    elif provider_name == "mock":
        from .mock_provider import MockProvider
        _provider_instance = MockProvider()
    # elif provider_name == "anthropic":
    #     from .anthropic_provider import AnthropicProvider
    #     _provider_instance = AnthropicProvider()
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")
    
    return _provider_instance