"""Fitness runner: orchestrates scoring of code candidates."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FitnessScore:
    """Individual fitness score for a code candidate."""

    correctness: float = 0.0
    performance: float = 0.0
    readability: float = 0.0
    robustness: float = 0.0
    security: float = 0.0

    @property
    def total(self) -> float:
        """Weighted total score (0-100)."""
        weights = {
            "correctness": 0.35,
            "performance": 0.15,
            "readability": 0.15,
            "robustness": 0.20,
            "security": 0.15,
        }
        raw = (
            self.correctness * weights["correctness"]
            + self.performance * weights["performance"]
            + self.readability * weights["readability"]
            + self.robustness * weights["robustness"]
            + self.security * weights["security"]
        )
        return round(raw, 2)


@dataclass
class CandidateResult:
    """A scored code candidate."""

    code: str
    fitness: FitnessScore
    generation: int = 0
    parent_indices: list[int] = field(default_factory=list)

    @property
    def rank_key(self) -> float:
        return self.fitness.total


class FitnessEvaluator:
    """Base class for fitness evaluators."""

    async def score(self, code: str, task: str) -> FitnessScore:
        """Score a code candidate. Override in subclasses."""
        return FitnessScore()


class FitnessRunner:
    """Runs fitness evaluation across multiple dimensions."""

    def __init__(self, evaluators: list[FitnessEvaluator] | None = None) -> None:
        self._evaluators: list[FitnessEvaluator] = evaluators or []

    def add_evaluator(self, evaluator: FitnessEvaluator) -> None:
        self._evaluators.append(evaluator)

    async def evaluate(self, code: str, task: str) -> FitnessScore:
        """Run all evaluators and combine scores."""
        score = FitnessScore()
        for evaluator in self._evaluators:
            partial = await evaluator.score(code, task)
            score.correctness = max(score.correctness, partial.correctness)
            score.performance = max(score.performance, partial.performance)
            score.readability = max(score.readability, partial.readability)
            score.robustness = max(score.robustness, partial.robustness)
            score.security = max(score.security, partial.security)
        return score

    async def rank_candidates(
        self, candidates: list[str], task: str
    ) -> list[CandidateResult]:
        """Score and rank a list of code candidates."""
        results = []
        for code in candidates:
            fitness = await self.evaluate(code, task)
            results.append(CandidateResult(code=code, fitness=fitness))
        results.sort(key=lambda r: r.rank_key, reverse=True)
        return results
