from dashboard.providers import PROVIDERS, get_provider, get_pricing


def test_all_providers_exist():
    assert "gemini" in PROVIDERS
    assert "openai" in PROVIDERS
    assert "grok" in PROVIDERS


def test_provider_has_required_fields():
    for name, p in PROVIDERS.items():
        assert "label" in p, f"{name} missing label"
        assert "base_url" in p, f"{name} missing base_url"
        assert "models" in p, f"{name} missing models"
        assert len(p["models"]) > 0, f"{name} has no models"


def test_get_provider():
    p = get_provider("gemini")
    assert p["label"] == "Google Gemini"
    assert "gemini" in p["models"][0]


def test_get_provider_unknown():
    p = get_provider("unknown")
    assert p is None


def test_get_pricing():
    price = get_pricing("gemini", "gemini-2.5-flash")
    assert "cost_per_1m_in" in price
    assert "cost_per_1m_out" in price
    assert price["cost_per_1m_in"] >= 0


def test_get_pricing_default():
    price = get_pricing("gemini", "nonexistent-model")
    assert price["cost_per_1m_in"] >= 0
