"""Hybrid authentication for all provider tiers."""

from __future__ import annotations

import os
import shutil

from pydantic import BaseModel

ENV_KEYS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
}


class ProviderAuth(BaseModel):
    """Authentication state for a single provider."""

    provider: str
    api_key: str = ""
    method: str = "none"
    available: bool = False

    @classmethod
    def from_env(cls, provider: str) -> ProviderAuth:
        if provider == "ollama":
            return cls(provider="ollama", method="local", available=True)

        env_key = ENV_KEYS.get(provider, "")
        api_key = os.environ.get(env_key, "")

        if api_key:
            return cls(provider=provider, api_key=api_key, method="api_key", available=True)

        # Check for CLI passthrough
        cli_name = "claude" if provider == "anthropic" else provider
        if shutil.which(cli_name):
            return cls(provider=provider, method="cli", available=True)

        return cls(provider=provider)


class AuthStatus(BaseModel):
    """Overall authentication status."""

    anthropic_available: bool
    openai_available: bool
    ollama_available: bool
    nvidia_available: bool = False
    degraded: bool = False
    available_stages: list[int] = []


class AuthManager:
    """Manages authentication across all providers."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderAuth] = {}
        for provider in ["anthropic", "openai", "ollama", "nvidia"]:
            self._providers[provider] = ProviderAuth.from_env(provider)

    def get(self, provider: str) -> ProviderAuth:
        return self._providers.get(provider, ProviderAuth(provider=provider))

    def status(self) -> AuthStatus:
        anthropic = self._providers["anthropic"].available
        openai = self._providers["openai"].available
        ollama = self._providers["ollama"].available
        nvidia = self._providers["nvidia"].available

        stages: list[int] = []
        if anthropic:
            stages.extend([1, 5])
        if openai:
            stages.append(2)
        if ollama:
            stages.append(3)
        if nvidia:
            stages.append(4)
        stages = sorted(set(stages))

        degraded = not (anthropic and openai)

        return AuthStatus(
            anthropic_available=anthropic,
            openai_available=openai,
            ollama_available=ollama,
            nvidia_available=nvidia,
            degraded=degraded,
            available_stages=stages,
        )
