import pytest
from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.core.result import Stage
from crowe_codex.strategies.consensus import Consensus


class FakeAgent(Agent):
    def __init__(self, response: str):
        super().__init__(config=AgentConfig(name="fake", provider="test"))
        self._response = response

    async def execute(self, prompt, context=None):
        return self._response

    async def is_available(self):
        return True


def test_consensus_required_stages():
    strategy = Consensus()
    assert Stage.ARCHITECT in strategy.required_stages
    assert Stage.BUILDER in strategy.required_stages
    assert Stage.DISPATCH in strategy.required_stages


@pytest.mark.asyncio
async def test_consensus_agreement():
    agents = {
        "claude": FakeAgent("def add(a, b): return a + b"),
        "codex": FakeAgent("def add(a, b): return a + b"),
        "dispatch": FakeAgent('{"code": "def add(a, b): return a + b", "agreement": true}'),
    }
    strategy = Consensus()
    result = await strategy.execute("add two numbers", agents)
    assert "claude_output" in result
    assert "codex_output" in result
    assert result["strategy"] == "consensus"


@pytest.mark.asyncio
async def test_consensus_disagreement():
    agents = {
        "claude": FakeAgent("def add(a, b): return a + b"),
        "codex": FakeAgent("def add(x, y): return x + y"),
        "dispatch": FakeAgent('{"code": "def add(a, b): return a + b", "agreement": false}'),
    }
    strategy = Consensus()
    result = await strategy.execute("add two numbers", agents)
    assert result["claude_output"] != result["codex_output"]
