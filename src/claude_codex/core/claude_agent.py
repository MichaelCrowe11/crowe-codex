"""Claude agent adapter for Stage 1 (Architect) and Stage 5 (Dispatch)."""

from __future__ import annotations

from anthropic import AsyncAnthropic

from claude_codex.core.agent import Agent, AgentConfig

DEFAULT_MODEL = "claude-opus-4-6"


class ClaudeAgent(Agent):
    """Claude agent for architecture planning and final dispatch."""

    def __init__(self, config: AgentConfig) -> None:
        super().__init__(config)
        self.model = config.model or DEFAULT_MODEL
        self._client: AsyncAnthropic | None = None

    def _get_client(self) -> AsyncAnthropic:
        if self._client is None:
            self._client = AsyncAnthropic(api_key=self.config.api_key or None)
        return self._client

    async def execute(self, prompt: str, context: dict[str, object] | None = None) -> str:
        client = self._get_client()
        message = await client.messages.create(
            model=self.model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    async def is_available(self) -> bool:
        return bool(self.config.api_key)

    def build_architect_prompt(self, task: str) -> str:
        return (
            "You are the ARCHITECT stage of the claude-codex pipeline.\n\n"
            "Your role:\n"
            "1. Decompose this task into atomic subtasks\n"
            "2. Define the architectural plan with types and interfaces\n"
            "3. Create an initial threat model\n"
            "4. Set acceptance criteria for downstream stages\n\n"
            f"Task: {task}\n\n"
            "Respond with a structured JSON plan containing:\n"
            '- "subtasks": list of subtask descriptions\n'
            '- "interfaces": key types/interfaces needed\n'
            '- "threat_model": potential security concerns\n'
            '- "acceptance_criteria": what each stage must verify\n'
        )

    def build_dispatch_prompt(self, task: str, stage_outputs: dict[str, str]) -> str:
        outputs_text = "\n\n".join(
            f"=== {stage} ===\n{output}" for stage, output in stage_outputs.items()
        )
        return (
            "You are the DISPATCH stage (final gate) of the claude-codex pipeline.\n\n"
            "Your role:\n"
            "1. Verify the final code matches the original architectural intent\n"
            "2. Perform OWASP Top 10 security sweep\n"
            "3. Resolve any conflicts between stage outputs\n"
            "4. Generate a confidence score and security attestation\n"
            "5. Produce the final, clean output\n\n"
            f"Original task: {task}\n\n"
            f"Stage outputs:\n{outputs_text}\n\n"
            "Respond with:\n"
            '- "code": the final verified code\n'
            '- "security_issues": list of any issues found (empty if clean)\n'
            '- "confidence": your confidence assessment\n'
            '- "summary": human-readable summary of what was built\n'
        )
