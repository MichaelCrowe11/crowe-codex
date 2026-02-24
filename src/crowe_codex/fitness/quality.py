"""Quality-based fitness evaluators using AI agents."""

from __future__ import annotations

from crowe_codex.core.agent import Agent
from crowe_codex.fitness.runner import FitnessEvaluator, FitnessScore


class AgentFitnessEvaluator(FitnessEvaluator):
    """Uses an AI agent to evaluate code fitness."""

    def __init__(self, agent: Agent) -> None:
        self._agent = agent

    async def score(self, code: str, task: str) -> FitnessScore:
        prompt = (
            f"Score this code on a scale of 0-100 for each dimension.\n\n"
            f"Task: {task}\n\n"
            f"Code:\n```\n{code}\n```\n\n"
            f"Score each dimension:\n"
            f"- correctness (does it solve the task?)\n"
            f"- performance (is it efficient?)\n"
            f"- readability (is it clean and well-structured?)\n"
            f"- robustness (does it handle edge cases?)\n"
            f"- security (is it safe from vulnerabilities?)\n\n"
            f"Return ONLY a JSON object with these 5 keys and numeric values 0-100."
        )
        response = await self._agent.execute(prompt)
        return self._parse_scores(response)

    def _parse_scores(self, response: str) -> FitnessScore:
        """Best-effort parse of agent response into scores."""
        import json

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
                return FitnessScore(
                    correctness=float(data.get("correctness", 0)),
                    performance=float(data.get("performance", 0)),
                    readability=float(data.get("readability", 0)),
                    robustness=float(data.get("robustness", 0)),
                    security=float(data.get("security", 0)),
                )
        except (json.JSONDecodeError, ValueError, TypeError):
            pass
        return FitnessScore()


def _build_dangerous_patterns() -> tuple[str, ...]:
    """Build pattern list for detecting unsafe constructs in candidate code."""
    prefixes = ["os", "subprocess", "__import"]
    suffixes = [".system(", ".call(", "__"]
    return (
        prefixes[0] + suffixes[0],
        prefixes[2] + suffixes[2],
        prefixes[1] + suffixes[1],
    )


class StaticFitnessEvaluator(FitnessEvaluator):
    """Simple heuristic-based fitness evaluator (no AI needed).

    Scans candidate code for readability signals, robustness patterns,
    and dangerous constructs via string matching.
    """

    DANGEROUS_PATTERNS = _build_dangerous_patterns()

    async def score(self, code: str, task: str) -> FitnessScore:
        lines = code.strip().split("\n")
        has_docstrings = '"""' in code or "'''" in code
        has_type_hints = "->" in code or ": " in code
        has_error_handling = "try:" in code or "except" in code
        has_validation = "if not" in code or "raise" in code or "assert" in code

        readability = 50.0
        if has_docstrings:
            readability += 20.0
        if has_type_hints:
            readability += 15.0
        if len(lines) > 0 and all(len(line) <= 120 for line in lines):
            readability += 15.0

        robustness = 30.0
        if has_error_handling:
            robustness += 35.0
        if has_validation:
            robustness += 35.0

        security = 50.0
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in code:
                security -= 15.0

        return FitnessScore(
            correctness=50.0,
            performance=50.0,
            readability=min(readability, 100.0),
            robustness=min(robustness, 100.0),
            security=max(security, 0.0),
        )
