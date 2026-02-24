"""Verification Loop: one writes code, another writes tests, cross-verify."""

from __future__ import annotations

from crowe_codex.core.agent import Agent
from crowe_codex.core.result import Stage
from crowe_codex.strategies.base import Strategy


class VerificationLoop(Strategy):
    """Cross-vendor verification: one agent codes, another tests, then swap."""

    name = "verification_loop"
    required_stages = [Stage.ARCHITECT, Stage.BUILDER, Stage.DISPATCH]

    def __init__(self, iterations: int = 2) -> None:
        self.iterations = iterations

    async def execute(
        self,
        task: str,
        agents: dict[str, Agent],
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        claude = agents["claude"]
        codex = agents["codex"]
        dispatch = agents["dispatch"]

        # Round 1: Claude codes, Codex writes tests
        code_prompt = (
            f"Write production-quality code for this task. Return ONLY code.\n\n"
            f"Task: {task}"
        )
        code_output = await claude.execute(code_prompt)

        test_prompt = (
            f"Write comprehensive tests for the following code. "
            f"Include edge cases, error conditions, and boundary values. "
            f"Return ONLY test code.\n\n"
            f"Code to test:\n```\n{code_output}\n```"
        )
        test_output = await codex.execute(test_prompt)

        all_code = [code_output]
        all_tests = [test_output]

        for i in range(1, self.iterations):
            # Swap: Codex reviews/fixes code based on tests
            fix_prompt = (
                f"Review this code against these tests. Fix any issues the tests "
                f"would catch. Return ONLY the fixed code.\n\n"
                f"Code:\n```\n{code_output}\n```\n\n"
                f"Tests:\n```\n{test_output}\n```"
            )
            # Alternate which agent fixes
            if i % 2 == 1:
                code_output = await codex.execute(fix_prompt)
            else:
                code_output = await claude.execute(fix_prompt)

            all_code.append(code_output)

            # Generate additional tests for the fixed code
            more_tests_prompt = (
                f"The code has been updated. Write additional tests that cover "
                f"any new behavior or remaining gaps.\n\n"
                f"Updated code:\n```\n{code_output}\n```\n\n"
                f"Existing tests:\n```\n{test_output}\n```"
            )
            if i % 2 == 1:
                test_output = await claude.execute(more_tests_prompt)
            else:
                test_output = await codex.execute(more_tests_prompt)

            all_tests.append(test_output)

        # Dispatch: final verdict
        dispatch_prompt = (
            f"Verify this code passes its tests and is production-ready.\n\n"
            f"Final code:\n```\n{code_output}\n```\n\n"
            f"Final tests:\n```\n{test_output}\n```\n\n"
            f"Iterations performed: {self.iterations}\n"
            f"Provide verdict and confidence score."
        )
        dispatch_output = await dispatch.execute(dispatch_prompt)

        return {
            "code_output": code_output,
            "test_output": test_output,
            "dispatch_output": dispatch_output,
            "iterations": self.iterations,
            "code_versions": len(all_code),
            "test_versions": len(all_tests),
            "strategy": self.name,
        }
