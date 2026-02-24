"""Abstract strategy base class."""

from __future__ import annotations

from abc import ABC, abstractmethod

from claude_codex.core.agent import Agent
from claude_codex.core.result import Stage


class Strategy(ABC):
    """Base class for all pipeline strategies."""

    name: str = ""
    required_stages: list[Stage] = []

    @abstractmethod
    async def execute(
        self,
        task: str,
        agents: dict[str, Agent],
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Execute this strategy and return results."""
        ...

    def stages_needed(self) -> list[int]:
        """Return sorted list of stage numbers this strategy requires."""
        return sorted(s.value for s in self.required_stages)
