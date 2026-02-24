"""Consensus strategy: same task, compare results, flag divergences."""

from __future__ import annotations

import asyncio

from claude_codex.core.agent import Agent
from claude_codex.core.result import Stage
from claude_codex.strategies.base import Strategy


class Consensus(Strategy):
    """Run the same task through multiple agents and compare results."""

    name = "consensus"
    required_stages = [Stage.ARCHITECT, Stage.BUILDER, Stage.DISPATCH]

    async def execute(
        self,
        task: str,
        agents: dict[str, Agent],
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        prompt = (
            f"Generate code for the following task. Return ONLY the code.\n\n"
            f"Task: {task}"
        )

        claude_task = agents["claude"].execute(prompt)
        codex_task = agents["codex"].execute(prompt)
        claude_output, codex_output = await asyncio.gather(claude_task, codex_task)

        dispatch_prompt = (
            "Compare these two implementations and produce the best final version.\n\n"
            f"Implementation A (Claude):\n{claude_output}\n\n"
            f"Implementation B (Codex):\n{codex_output}\n\n"
            "Respond with JSON containing:\n"
            '- "code": the best implementation\n'
            '- "agreement": true if both are functionally equivalent\n'
            '- "confidence": float 0-1\n'
            '- "divergences": list of differences if any\n'
        )
        dispatch_output = await agents["dispatch"].execute(dispatch_prompt)

        return {
            "claude_output": claude_output,
            "codex_output": codex_output,
            "dispatch_output": dispatch_output,
            "strategy": self.name,
        }
