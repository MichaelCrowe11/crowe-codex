"""Adaptive Router: learns which strategy works best per task type."""

from __future__ import annotations

import json
from pathlib import Path

from crowe_codex.core.agent import Agent
from crowe_codex.core.result import Stage
from crowe_codex.strategies.base import Strategy


# Keywords that suggest task complexity/domain
TASK_SIGNALS: dict[str, list[str]] = {
    "security": ["security", "auth", "encrypt", "xss", "injection", "owasp", "vulnerability"],
    "performance": ["optimize", "fast", "performance", "benchmark", "cache", "latency"],
    "simple": ["simple", "basic", "hello", "print", "trivial", "small"],
    "complex": ["architecture", "system", "distributed", "microservice", "pipeline"],
    "testing": ["test", "coverage", "verify", "validate", "assert"],
}

# Default strategy recommendations per signal
DEFAULT_ROUTING: dict[str, str] = {
    "security": "adversarial",
    "performance": "evolutionary",
    "simple": "consensus",
    "complex": "pipeline",
    "testing": "verification_loop",
}


class RoutingHistory:
    """Persists routing decisions and outcomes for learning."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path.home() / ".claude" / "crowe-logic" / "routing-history.json"
        self._history: list[dict[str, object]] = []
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._history = json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                self._history = []

    def record(self, task: str, strategy: str, score: float) -> None:
        """Record a routing decision and its outcome score."""
        self._history.append({
            "task_signals": self._extract_signals(task),
            "strategy": strategy,
            "score": score,
        })
        self._save()

    def best_strategy_for(self, task: str) -> str | None:
        """Look up the best-performing strategy for similar tasks."""
        signals = self._extract_signals(task)
        if not signals or not self._history:
            return None

        # Find entries with overlapping signals
        candidates: dict[str, list[float]] = {}
        for entry in self._history:
            entry_signals = entry.get("task_signals", [])
            if set(signals) & set(entry_signals):
                strategy = str(entry["strategy"])
                candidates.setdefault(strategy, []).append(float(entry["score"]))

        if not candidates:
            return None

        # Return strategy with highest average score
        best = max(candidates, key=lambda s: sum(candidates[s]) / len(candidates[s]))
        return best

    def _extract_signals(self, task: str) -> list[str]:
        task_lower = task.lower()
        return [
            signal
            for signal, keywords in TASK_SIGNALS.items()
            if any(kw in task_lower for kw in keywords)
        ]

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._history, indent=2))


class AdaptiveRouter(Strategy):
    """Routes tasks to the best strategy based on learned history."""

    name = "adaptive_router"
    required_stages = [Stage.ARCHITECT, Stage.DISPATCH]

    def __init__(
        self,
        strategies: dict[str, Strategy] | None = None,
        history: RoutingHistory | None = None,
    ) -> None:
        self._strategies = strategies or {}
        self._history = history or RoutingHistory()

    def register_strategy(self, strategy: Strategy) -> None:
        self._strategies[strategy.name] = strategy

    def select_strategy(self, task: str) -> Strategy:
        """Pick the best strategy for a given task."""
        # Check learned history first
        learned = self._history.best_strategy_for(task)
        if learned and learned in self._strategies:
            return self._strategies[learned]

        # Fall back to keyword-based routing
        task_lower = task.lower()
        for signal, keywords in TASK_SIGNALS.items():
            if any(kw in task_lower for kw in keywords):
                recommended = DEFAULT_ROUTING.get(signal)
                if recommended and recommended in self._strategies:
                    return self._strategies[recommended]

        # Default: consensus (lowest cost)
        if "consensus" in self._strategies:
            return self._strategies["consensus"]

        # Fallback: first available strategy
        return next(iter(self._strategies.values()))

    async def execute(
        self,
        task: str,
        agents: dict[str, Agent],
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        selected = self.select_strategy(task)
        result = await selected.execute(task, agents, context)
        result["routed_to"] = selected.name
        result["strategy"] = self.name
        return result
