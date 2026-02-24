"""Abstract agent interface and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    name: str
    provider: str
    model: str = ""
    api_key: str = ""
    base_url: str = ""


class Agent(ABC):
    """Abstract base for all agents in the pipeline."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config

    @abstractmethod
    async def execute(self, prompt: str, context: dict[str, object] | None = None) -> str:
        """Execute a prompt and return the response."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if this agent is currently available."""
        ...


class AgentRegistry:
    """Registry of available agents."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, name: str, agent: Agent) -> None:
        self._agents[name] = agent

    def get(self, name: str) -> Agent:
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' not registered")
        return self._agents[name]

    def available(self) -> list[str]:
        return list(self._agents.keys())
