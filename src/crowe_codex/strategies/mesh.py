"""Cognitive Mesh: parallel execution with intelligent merge."""

from __future__ import annotations

import asyncio

from crowe_codex.core.agent import Agent
from crowe_codex.core.result import Stage
from crowe_codex.strategies.base import Strategy


class CognitiveMesh(Strategy):
    """All available agents work in parallel; dispatch merges the best parts."""

    name = "cognitive_mesh"
    required_stages = [Stage.ARCHITECT, Stage.BUILDER, Stage.DISPATCH]

    async def execute(
        self,
        task: str,
        agents: dict[str, Agent],
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        dispatch = agents["dispatch"]

        # Identify all worker agents (everything except dispatch)
        workers = {k: v for k, v in agents.items() if k != "dispatch"}

        prompt = (
            f"Generate code for the following task. Return ONLY the code.\n\n"
            f"Task: {task}"
        )

        # Fire all workers in parallel
        tasks = {
            name: agent.execute(prompt)
            for name, agent in workers.items()
        }
        results = dict(
            zip(tasks.keys(), await asyncio.gather(*tasks.values()))
        )

        # Build comparison prompt for dispatch
        comparison_parts = []
        for name, output in results.items():
            comparison_parts.append(
                f"--- {name.upper()} ---\n{output}"
            )

        merge_prompt = (
            f"You are merging outputs from {len(results)} independent AI agents "
            f"who all solved the same task.\n\n"
            f"Task: {task}\n\n"
            + "\n\n".join(comparison_parts)
            + "\n\nAnalyze each solution. Produce the BEST possible implementation by:\n"
            "1. Identifying the strongest parts of each solution\n"
            "2. Combining the best approaches\n"
            "3. Resolving any conflicts\n\n"
            "Return the merged code and a confidence assessment."
        )
        dispatch_output = await dispatch.execute(merge_prompt)

        return {
            **{f"{name}_output": output for name, output in results.items()},
            "dispatch_output": dispatch_output,
            "agents_consulted": len(results),
            "strategy": self.name,
        }
