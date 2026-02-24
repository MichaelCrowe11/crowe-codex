import pytest
from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.core.result import Stage
from crowe_codex.strategies.mesh import CognitiveMesh


class FakeAgent(Agent):
    def __init__(self, response: str):
        super().__init__(config=AgentConfig(name="fake", provider="test"))
        self._response = response
        self.call_count = 0

    async def execute(self, prompt, context=None):
        self.call_count += 1
        return self._response

    async def is_available(self):
        return True


def test_mesh_required_stages():
    strategy = CognitiveMesh()
    assert Stage.ARCHITECT in strategy.required_stages
    assert Stage.BUILDER in strategy.required_stages
    assert Stage.DISPATCH in strategy.required_stages


def test_mesh_name():
    assert CognitiveMesh().name == "cognitive_mesh"


@pytest.mark.asyncio
async def test_mesh_parallel_execution():
    agents = {
        "claude": FakeAgent("claude solution"),
        "codex": FakeAgent("codex solution"),
        "ollama": FakeAgent("ollama solution"),
        "dispatch": FakeAgent("merged result"),
    }
    strategy = CognitiveMesh()
    result = await strategy.execute("build something", agents)
    assert result["strategy"] == "cognitive_mesh"
    assert result["agents_consulted"] == 3  # all except dispatch
    assert result["claude_output"] == "claude solution"
    assert result["codex_output"] == "codex solution"
    assert result["ollama_output"] == "ollama solution"
    assert result["dispatch_output"] == "merged result"


@pytest.mark.asyncio
async def test_mesh_two_agents():
    agents = {
        "claude": FakeAgent("claude code"),
        "dispatch": FakeAgent("merged"),
    }
    strategy = CognitiveMesh()
    result = await strategy.execute("task", agents)
    assert result["agents_consulted"] == 1
    assert result["claude_output"] == "claude code"


@pytest.mark.asyncio
async def test_mesh_all_agents_called():
    claude = FakeAgent("c")
    codex = FakeAgent("x")
    dispatch = FakeAgent("merged")

    agents = {"claude": claude, "codex": codex, "dispatch": dispatch}
    strategy = CognitiveMesh()
    await strategy.execute("task", agents)
    assert claude.call_count == 1
    assert codex.call_count == 1
    assert dispatch.call_count == 1  # merge step
