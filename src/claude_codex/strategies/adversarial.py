"""Adversarial Synthesis: one builds, one attacks, one fuzzes."""

from __future__ import annotations

from claude_codex.core.agent import Agent
from claude_codex.core.result import Stage
from claude_codex.strategies.base import Strategy


class Adversarial(Strategy):
    """Adversarial code synthesis with cross-vendor attack/defense cycles."""

    name = "adversarial"
    required_stages = [Stage.ARCHITECT, Stage.BUILDER, Stage.SPECIALIST, Stage.DISPATCH]

    def __init__(self, rounds: int = 1) -> None:
        self.rounds = rounds

    async def execute(
        self,
        task: str,
        agents: dict[str, Agent],
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        claude = agents["claude"]
        codex = agents["codex"]
        ollama = agents["ollama"]
        dispatch = agents["dispatch"]

        # Stage 1: Claude architects
        build_prompt = (
            f"Write production-quality code for this task. Return ONLY code.\n\n"
            f"Task: {task}"
        )
        build_output = await claude.execute(build_prompt)

        attack_output = ""
        fuzz_output = ""
        all_attacks: list[str] = []
        all_fuzzes: list[str] = []

        for round_num in range(self.rounds):
            # Stage 2: Codex attacks
            attack_prompt = (
                f"You are a security adversary. Find vulnerabilities, edge cases, and "
                f"potential exploits in this code. Be thorough and aggressive.\n\n"
                f"Code to attack:\n```\n{build_output}\n```\n\n"
                f"List every issue you find with severity ratings."
            )
            attack_output = await codex.execute(attack_prompt)
            all_attacks.append(attack_output)

            # Stage 3: Ollama fuzzes
            fuzz_prompt = (
                f"Generate adversarial inputs and edge cases for this code. "
                f"Try to break it with unexpected types, boundary values, "
                f"injection attempts, and malformed data.\n\n"
                f"Code to fuzz:\n```\n{build_output}\n```"
            )
            fuzz_output = await ollama.execute(fuzz_prompt)
            all_fuzzes.append(fuzz_output)

            # Claude fixes based on attacks + fuzzing
            if round_num < self.rounds - 1:
                fix_prompt = (
                    f"Your code was attacked and fuzzed. Fix ALL issues found.\n\n"
                    f"Original code:\n```\n{build_output}\n```\n\n"
                    f"Attacks found:\n{attack_output}\n\n"
                    f"Fuzz results:\n{fuzz_output}\n\n"
                    f"Return the hardened code only."
                )
                build_output = await claude.execute(fix_prompt)

        # Stage 5: Dispatch final verification
        dispatch_prompt = (
            f"Final verification. Review code that survived adversarial testing.\n\n"
            f"Final code:\n```\n{build_output}\n```\n\n"
            f"Attacks it survived:\n{chr(10).join(all_attacks)}\n\n"
            f"Fuzz tests it survived:\n{chr(10).join(all_fuzzes)}\n\n"
            "Provide final verdict and confidence score."
        )
        dispatch_output = await dispatch.execute(dispatch_prompt)

        return {
            "build_output": build_output,
            "attack_output": attack_output,
            "fuzz_output": fuzz_output,
            "dispatch_output": dispatch_output,
            "rounds": self.rounds,
            "total_attacks": len(all_attacks),
            "strategy": self.name,
        }
