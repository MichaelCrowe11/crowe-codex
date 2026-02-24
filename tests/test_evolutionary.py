import pytest
from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.core.result import Stage
from crowe_codex.strategies.evolutionary import Evolutionary


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


def test_evolutionary_required_stages():
    strategy = Evolutionary()
    assert Stage.ARCHITECT in strategy.required_stages
    assert Stage.BUILDER in strategy.required_stages
    assert Stage.SPECIALIST in strategy.required_stages
    assert Stage.DISPATCH in strategy.required_stages


def test_evolutionary_name():
    assert Evolutionary().name == "evolutionary"


def test_evolutionary_defaults():
    strategy = Evolutionary()
    assert strategy.population == 3
    assert strategy.generations == 2


@pytest.mark.asyncio
async def test_evolutionary_single_generation():
    agents = {
        "claude": FakeAgent("candidate A"),
        "codex": FakeAgent("candidate B"),
        "ollama": FakeAgent("scores: A=8, B=7"),
        "dispatch": FakeAgent("winner: candidate A"),
    }
    strategy = Evolutionary(population=2, generations=1)
    result = await strategy.execute("optimize sorting", agents)
    assert result["strategy"] == "evolutionary"
    assert result["generations"] == 1
    assert result["population"] == 2
    assert len(result["candidates"]) == 2
    assert "dispatch_output" in result


@pytest.mark.asyncio
async def test_evolutionary_multiple_generations():
    claude = FakeAgent("evolved code---CANDIDATE---even better")
    codex = FakeAgent("candidate")
    ollama = FakeAgent("fitness: 8/10")
    dispatch = FakeAgent("best candidate selected")

    agents = {
        "claude": claude,
        "codex": codex,
        "ollama": ollama,
        "dispatch": dispatch,
    }
    strategy = Evolutionary(population=2, generations=3)
    result = await strategy.execute("build parser", agents)
    assert result["generations"] == 3
    assert result["total_candidates_evaluated"] >= 6  # 2 per gen * 3 gens


@pytest.mark.asyncio
async def test_evolutionary_population_maintained():
    """Ensure population size is maintained across generations."""
    agents = {
        "claude": FakeAgent("code---CANDIDATE---code2---CANDIDATE---code3"),
        "codex": FakeAgent("alt code"),
        "ollama": FakeAgent("all good"),
        "dispatch": FakeAgent("winner"),
    }
    strategy = Evolutionary(population=3, generations=2)
    result = await strategy.execute("task", agents)
    assert len(result["candidates"]) == 3
