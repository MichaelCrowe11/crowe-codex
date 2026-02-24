"""Codex agent adapter for Stage 2 (Builder)."""

from __future__ import annotations

import json

from openai import AsyncOpenAI

from claude_codex.core.agent import Agent, AgentConfig

DEFAULT_MODEL = "gpt-5.3"


class CodexAgent(Agent):
    """Codex/GPT agent for code generation and testing."""

    def __init__(self, config: AgentConfig) -> None:
        super().__init__(config)
        self.model = config.model or DEFAULT_MODEL
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            kwargs: dict[str, str] = {}
            if self.config.api_key:
                kwargs["api_key"] = self.config.api_key
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def execute(self, prompt: str, context: dict[str, object] | None = None) -> str:
        client = self._get_client()
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
        )
        return response.choices[0].message.content or ""

    async def is_available(self) -> bool:
        return bool(self.config.api_key)

    def build_builder_prompt(self, blueprint: dict[str, object]) -> str:
        blueprint_text = json.dumps(blueprint, indent=2)
        return (
            "You are the BUILDER stage of the claude-codex pipeline.\n\n"
            "Your role:\n"
            "1. Implement the code according to the architect's blueprint\n"
            "2. Write comprehensive test suites\n"
            "3. Ensure all acceptance criteria are met\n"
            "4. Flag any blueprint ambiguities\n\n"
            f"Blueprint:\n{blueprint_text}\n\n"
            "Respond with:\n"
            '- "code": the complete implementation\n'
            '- "tests": test suite code\n'
            '- "ambiguities": any unclear requirements (empty list if none)\n'
        )
