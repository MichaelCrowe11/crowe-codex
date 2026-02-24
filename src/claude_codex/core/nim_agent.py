"""NVIDIA NIM agent adapter for Stage 4 (Accelerator). Stub for v0.1.0."""

from __future__ import annotations

from claude_codex.core.agent import Agent, AgentConfig


class NimAgent(Agent):
    """NVIDIA NIM agent for GPU-accelerated batch inference.

    This is a stub for v0.1.0. Full implementation in v1.5.0.
    """

    def __init__(self, config: AgentConfig) -> None:
        super().__init__(config)

    async def execute(self, prompt: str, context: dict[str, object] | None = None) -> str:
        if not await self.is_available():
            raise RuntimeError(
                "NVIDIA NIM is not configured. Set NVIDIA_API_KEY or upgrade to Enterprise tier."
            )
        raise NotImplementedError("NVIDIA NIM integration coming in v1.5.0")

    async def is_available(self) -> bool:
        return bool(self.config.api_key)
