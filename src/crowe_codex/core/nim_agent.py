"""NVIDIA NIM agent adapter for Stage 4 (Accelerator)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from crowe_codex.core.agent import Agent, AgentConfig


# NIM microservice endpoints for different tasks
NIM_ENDPOINTS = {
    "code-review": "nvidia/code-review",
    "code-gen": "nvidia/code-generation",
    "vulnerability-scan": "nvidia/security-scan",
    "optimization": "nvidia/code-optimization",
}


@dataclass
class NimBatchRequest:
    """A batch of prompts for GPU-accelerated inference."""

    prompts: list[str] = field(default_factory=list)
    model: str = ""
    max_tokens: int = 4096
    temperature: float = 0.1


@dataclass
class NimBatchResult:
    """Results from a NIM batch inference call."""

    responses: list[str] = field(default_factory=list)
    model: str = ""
    total_tokens: int = 0
    latency_ms: float = 0.0


class NimAgent(Agent):
    """NVIDIA NIM agent for GPU-accelerated batch inference.

    Uses NVIDIA NIM microservices for high-throughput code analysis.
    Falls back gracefully when NIM is unavailable.
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        batch_size: int = 5,
    ) -> None:
        if config is None:
            config = AgentConfig(
                name="nim",
                provider="nvidia",
                model="nvidia/nemotron-4-340b",
            )
        super().__init__(config)
        self.batch_size = batch_size
        self._client = None

    async def execute(self, prompt: str, context: dict[str, object] | None = None) -> str:
        """Execute a single prompt via NIM."""
        if not await self.is_available():
            return await self._fallback_execute(prompt)

        try:
            return await self._nim_execute(prompt)
        except Exception:
            return await self._fallback_execute(prompt)

    async def batch_execute(self, prompts: list[str]) -> list[str]:
        """Execute multiple prompts in parallel batches via NIM."""
        if not await self.is_available():
            return [await self._fallback_execute(p) for p in prompts]

        results = []
        for i in range(0, len(prompts), self.batch_size):
            batch = prompts[i : i + self.batch_size]
            batch_results = await asyncio.gather(
                *(self._nim_execute(p) for p in batch),
                return_exceptions=True,
            )
            for r in batch_results:
                if isinstance(r, Exception):
                    results.append(f"NIM error: {r}")
                else:
                    results.append(r)
        return results

    async def is_available(self) -> bool:
        """Check if NIM is configured and reachable."""
        return bool(self.config.api_key)

    async def _nim_execute(self, prompt: str) -> str:
        """Execute via NVIDIA NIM API (OpenAI-compatible endpoint)."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            return await self._fallback_execute(prompt)

        if self._client is None:
            base_url = self.config.base_url or "https://integrate.api.nvidia.com/v1"
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=base_url,
            )

        response = await self._client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    async def _fallback_execute(self, prompt: str) -> str:
        """Fallback when NIM is unavailable — return a pass-through marker."""
        return f"[NIM_UNAVAILABLE] Stage 4 skipped. Prompt: {prompt[:100]}..."

    def build_accelerator_prompt(self, code: str, task: str = "") -> str:
        """Build a prompt optimized for NIM's code analysis capabilities."""
        return (
            "You are an advanced code optimization engine. Analyze this code "
            "for performance bottlenecks, memory efficiency, and GPU-acceleration "
            "opportunities.\n\n"
            f"Code:\n```\n{code}\n```\n\n"
            f"{'Task context: ' + task + chr(10) + chr(10) if task else ''}"
            "Provide:\n"
            "1. Performance bottlenecks identified\n"
            "2. Memory optimization opportunities\n"
            "3. Parallelization potential\n"
            "4. Optimized code version\n"
        )
