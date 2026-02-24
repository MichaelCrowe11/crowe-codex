import pytest
from crowe_codex.core.result import Stage
from crowe_codex.strategies.base import Strategy


def test_strategy_is_abstract():
    with pytest.raises(TypeError):
        Strategy()


class MockStrategy(Strategy):
    name = "mock"
    required_stages = [Stage.ARCHITECT, Stage.DISPATCH]

    async def execute(self, task, agents, context=None):
        return {"code": "pass", "summary": "mock"}


def test_concrete_strategy():
    strategy = MockStrategy()
    assert strategy.name == "mock"
    assert Stage.ARCHITECT in strategy.required_stages
    assert Stage.DISPATCH in strategy.required_stages


def test_strategy_stages_needed():
    strategy = MockStrategy()
    assert strategy.stages_needed() == [1, 5]
