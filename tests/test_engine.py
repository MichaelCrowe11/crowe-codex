import pytest
from crowe_codex.core.agent import AgentConfig
from crowe_codex.core.engine import DualEngine
from crowe_codex.core.result import PipelineResult
from crowe_codex.strategies.consensus import Consensus


class FakeAgent:
    def __init__(self, name, response="ok"):
        self.config = AgentConfig(name=name, provider="test")
        self._response = response

    async def execute(self, prompt, context=None):
        return self._response

    async def is_available(self):
        return True


def test_engine_instantiation():
    engine = DualEngine(auto_detect=False)
    assert engine is not None


def test_engine_register_agents():
    engine = DualEngine(auto_detect=False)
    engine.register_agent("claude", FakeAgent("claude"))
    engine.register_agent("codex", FakeAgent("codex"))
    assert "claude" in engine.available_agents()
    assert "codex" in engine.available_agents()


@pytest.mark.asyncio
async def test_engine_run_consensus():
    engine = DualEngine(auto_detect=False)
    engine.register_agent("claude", FakeAgent("claude", "def add(a,b): return a+b"))
    engine.register_agent("codex", FakeAgent("codex", "def add(a,b): return a+b"))
    engine.register_agent("dispatch", FakeAgent("dispatch", '{"code":"pass"}'))

    result = await engine.run(Consensus(), task="add two numbers")
    assert isinstance(result, PipelineResult)
    assert result.code is not None


def test_engine_available_stages():
    engine = DualEngine(auto_detect=False)
    engine.register_agent("claude", FakeAgent("claude"))
    engine.register_agent("dispatch", FakeAgent("dispatch"))
    stages = engine.available_stages()
    assert 1 in stages
    assert 5 in stages
