from crowe_codex.core.auth import AuthManager, ProviderAuth


def test_provider_auth_from_env_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
    auth = ProviderAuth.from_env("anthropic")
    assert auth.api_key == "sk-test-123"
    assert auth.method == "api_key"


def test_provider_auth_missing_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Also ensure no CLI passthrough
    monkeypatch.setattr("shutil.which", lambda x: None)
    auth = ProviderAuth.from_env("anthropic")
    assert auth.api_key == ""
    assert auth.available is False


def test_provider_auth_ollama_always_available():
    auth = ProviderAuth.from_env("ollama")
    assert auth.method == "local"
    assert auth.available is True


def test_auth_manager_detects_available_providers(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr("shutil.which", lambda x: None)
    manager = AuthManager()
    status = manager.status()
    assert status.anthropic_available is True
    assert status.openai_available is False
    assert status.ollama_available is True


def test_auth_manager_degraded_mode(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.setattr("shutil.which", lambda x: None)
    manager = AuthManager()
    status = manager.status()
    assert status.degraded is True
    assert 1 in status.available_stages
    assert 5 in status.available_stages
    assert 3 in status.available_stages
    assert 2 not in status.available_stages
