"""AI provider configurations: endpoints, models, and pricing."""

PROVIDERS = {
    "gemini": {
        "label": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "key_prefix": "AIza",
        "models": [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
        ],
        "pricing": {
            "gemini-2.5-flash": {"cost_per_1m_in": 0.15, "cost_per_1m_out": 0.60},
            "gemini-2.5-pro": {"cost_per_1m_in": 1.25, "cost_per_1m_out": 10.00},
            "gemini-2.0-flash": {"cost_per_1m_in": 0.10, "cost_per_1m_out": 0.40},
            "gemini-2.0-flash-lite": {"cost_per_1m_in": 0.075, "cost_per_1m_out": 0.30},
        },
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "key_prefix": "sk-",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4.1-nano",
            "gpt-4.1-mini",
        ],
        "pricing": {
            "gpt-4o": {"cost_per_1m_in": 2.50, "cost_per_1m_out": 10.00},
            "gpt-4o-mini": {"cost_per_1m_in": 0.15, "cost_per_1m_out": 0.60},
            "gpt-4.1-nano": {"cost_per_1m_in": 0.10, "cost_per_1m_out": 0.40},
            "gpt-4.1-mini": {"cost_per_1m_in": 0.40, "cost_per_1m_out": 1.60},
        },
    },
    "grok": {
        "label": "xAI Grok",
        "base_url": "https://api.x.ai/v1",
        "key_env": "XAI_API_KEY",
        "key_prefix": "xai-",
        "models": [
            "grok-3-mini",
            "grok-3",
        ],
        "pricing": {
            "grok-3-mini": {"cost_per_1m_in": 0.30, "cost_per_1m_out": 0.50},
            "grok-3": {"cost_per_1m_in": 3.00, "cost_per_1m_out": 15.00},
        },
    },
}

DEFAULT_PRICING = {"cost_per_1m_in": 0.50, "cost_per_1m_out": 2.00}


def get_provider(name: str) -> dict | None:
    return PROVIDERS.get(name)


def get_pricing(provider_name: str, model_name: str) -> dict:
    provider = PROVIDERS.get(provider_name)
    if not provider:
        return DEFAULT_PRICING
    return provider["pricing"].get(model_name, DEFAULT_PRICING)


def provider_names() -> list[str]:
    return list(PROVIDERS.keys())


def provider_labels() -> list[str]:
    return [p["label"] for p in PROVIDERS.values()]
