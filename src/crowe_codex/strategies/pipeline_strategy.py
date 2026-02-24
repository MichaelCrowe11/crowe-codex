"""Pipeline Strategy: sequential handoff through the full stage chain."""

from __future__ import annotations

from crowe_codex.core.agent import Agent
from crowe_codex.core.result import Stage
from crowe_codex.strategies.base import Strategy


class Pipeline(Strategy):
    """Sequential pipeline: each stage refines the previous stage's output."""

    name = "pipeline"
    required_stages = [Stage.ARCHITECT, Stage.BUILDER, Stage.SPECIALIST, Stage.DISPATCH]

    def __init__(self, include_specialist: bool = True) -> None:
        self.include_specialist = include_specialist

    async def execute(
        self,
        task: str,
        agents: dict[str, Agent],
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        claude = agents["claude"]
        codex = agents["codex"]
        dispatch = agents["dispatch"]

        # Stage 1: Claude architects the solution
        architect_prompt = (
            f"Design the architecture and write an implementation plan for:\n\n"
            f"Task: {task}\n\n"
            f"Include: function signatures, data structures, error handling approach, "
            f"and key design decisions. Return a detailed blueprint."
        )
        architect_output = await claude.execute(architect_prompt)

        # Stage 2: Codex builds from the blueprint
        build_prompt = (
            f"Implement production-quality code from this architecture blueprint. "
            f"Follow the design exactly. Return ONLY code.\n\n"
            f"Blueprint:\n{architect_output}"
        )
        build_output = await codex.execute(build_prompt)

        # Stage 3: Specialist reviews (if available and enabled)
        specialist_output = ""
        if self.include_specialist and "ollama" in agents:
            specialist_prompt = (
                f"Review this implementation for domain-specific issues, "
                f"performance concerns, and edge cases.\n\n"
                f"Original task: {task}\n\n"
                f"Architecture:\n{architect_output}\n\n"
                f"Implementation:\n```\n{build_output}\n```\n\n"
                f"List issues and suggested improvements."
            )
            specialist_output = await agents["ollama"].execute(specialist_prompt)

        # Stage 5: Dispatch verifies and produces final output
        dispatch_input = (
            f"Final verification of pipeline output.\n\n"
            f"Task: {task}\n\n"
            f"Architecture:\n{architect_output}\n\n"
            f"Implementation:\n```\n{build_output}\n```\n"
        )
        if specialist_output:
            dispatch_input += f"\nSpecialist review:\n{specialist_output}\n"
        dispatch_input += "\nProvide final verdict, confidence score, and the approved code."

        dispatch_output = await dispatch.execute(dispatch_input)

        return {
            "architect_output": architect_output,
            "build_output": build_output,
            "specialist_output": specialist_output,
            "dispatch_output": dispatch_output,
            "stages_run": 4 if specialist_output else 3,
            "strategy": self.name,
        }
