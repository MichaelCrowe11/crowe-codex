"""Evolutionary Generation: multiple candidates, fitness-scored, best traits combined."""

from __future__ import annotations

import asyncio

from crowe_codex.core.agent import Agent
from crowe_codex.core.result import Stage
from crowe_codex.strategies.base import Strategy


class Evolutionary(Strategy):
    """Generate multiple code candidates, score them, breed the best traits."""

    name = "evolutionary"
    required_stages = [Stage.ARCHITECT, Stage.BUILDER, Stage.SPECIALIST, Stage.DISPATCH]

    def __init__(self, population: int = 3, generations: int = 2) -> None:
        self.population = population
        self.generations = generations

    async def execute(
        self,
        task: str,
        agents: dict[str, Agent],
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        claude = agents["claude"]
        codex = agents["codex"]
        dispatch = agents["dispatch"]

        # Collect all worker agents for candidate generation
        workers = [v for k, v in agents.items() if k != "dispatch"]

        all_generations: list[list[str]] = []

        # Generation 0: Initial population
        gen_prompt = (
            f"Write a complete, production-quality solution for this task. "
            f"Be creative and consider multiple approaches.\n\n"
            f"Task: {task}\n\n"
            f"Return ONLY code."
        )

        gen_tasks = []
        for i in range(self.population):
            agent = workers[i % len(workers)]
            variant_prompt = (
                f"{gen_prompt}\n\nVariant #{i + 1}: "
                f"Emphasize {'performance' if i % 3 == 0 else 'readability' if i % 3 == 1 else 'robustness'}."
            )
            gen_tasks.append(agent.execute(variant_prompt))

        candidates = list(await asyncio.gather(*gen_tasks))
        all_generations.append(list(candidates))

        # Evolution loop
        for gen in range(1, self.generations):
            # Fitness evaluation by specialist
            evaluator = agents.get("ollama", codex)
            fitness_prompt = (
                f"Rank these {len(candidates)} code candidates for the task: {task}\n\n"
            )
            for idx, c in enumerate(candidates):
                fitness_prompt += f"--- Candidate {idx + 1} ---\n{c}\n\n"
            fitness_prompt += (
                "Score each candidate 1-10 on: correctness, performance, "
                "readability, robustness. Return rankings."
            )
            fitness_output = await evaluator.execute(fitness_prompt)

            # Crossover: combine best traits
            crossover_prompt = (
                f"You've evaluated these candidates:\n{fitness_output}\n\n"
                f"Now produce {self.population} improved candidates by combining "
                f"the best traits. Fix any issues found. Return ONLY code for each "
                f"candidate, separated by '---CANDIDATE---'.\n\n"
                f"Original candidates:\n"
            )
            for idx, c in enumerate(candidates):
                crossover_prompt += f"--- Candidate {idx + 1} ---\n{c}\n\n"

            crossover_output = await claude.execute(crossover_prompt)
            candidates = [
                c.strip()
                for c in crossover_output.split("---CANDIDATE---")
                if c.strip()
            ]
            # Ensure we maintain population size
            while len(candidates) < self.population:
                candidates.append(candidates[-1] if candidates else "")
            candidates = candidates[: self.population]
            all_generations.append(list(candidates))

        # Final selection by dispatch
        final_prompt = (
            f"Select the best candidate from the final generation.\n\n"
            f"Task: {task}\n\n"
        )
        for idx, c in enumerate(candidates):
            final_prompt += f"--- Candidate {idx + 1} ---\n{c}\n\n"
        final_prompt += (
            "Pick the best one. Return the winning code and explain why."
        )
        dispatch_output = await dispatch.execute(final_prompt)

        return {
            "candidates": candidates,
            "generations": len(all_generations),
            "population": self.population,
            "dispatch_output": dispatch_output,
            "total_candidates_evaluated": sum(len(g) for g in all_generations),
            "strategy": self.name,
        }
