import pytest
from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.core.result import Stage
from crowe_codex.strategies.pipeline_strategy import Pipeline


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


def test_pipeline_required_stages():
    strategy = Pipeline()
    assert Stage.ARCHITECT in strategy.required_stages
    assert Stage.BUILDER in strategy.required_stages
    assert Stage.SPECIALIST in strategy.required_stages
    assert Stage.DISPATCH in strategy.required_stages


def test_pipeline_name():
    assert Pipeline().name == "pipeline"


@pytest.mark.asyncio
async def test_pipeline_full_run():
    agents = {
        "claude": FakeAgent("architecture blueprint"),
        "codex": FakeAgent("implemented code"),
        "ollama": FakeAgent("specialist review: looks good"),
        "dispatch": FakeAgent("approved"),
    }
    strategy = Pipeline()
    result = await strategy.execute("build an API", agents)
    assert result["strategy"] == "pipeline"
    assert result["stages_run"] == 4
    assert result["architect_output"] == "architecture blueprint"
    assert result["build_output"] == "implemented code"
    assert result["specialist_output"] == "specialist review: looks good"
    assert result["dispatch_output"] == "approved"


@pytest.mark.asyncio
async def test_pipeline_without_specialist():
    agents = {
        "claude": FakeAgent("blueprint"),
        "codex": FakeAgent("code"),
        "dispatch": FakeAgent("ok"),
    }
    strategy = Pipeline(include_specialist=False)
    result = await strategy.execute("simple task", agents)
    assert result["stages_run"] == 3
    assert result["specialist_output"] == ""


@pytest.mark.asyncio
async def test_pipeline_no_ollama_agent():
    """When ollama agent is missing, specialist stage is skipped."""
    agents = {
        "claude": FakeAgent("blueprint"),
        "codex": FakeAgent("code"),
        "dispatch": FakeAgent("ok"),
    }
    strategy = Pipeline(include_specialist=True)
    result = await strategy.execute("task", agents)
    assert result["stages_run"] == 3
    assert result["specialist_output"] == ""
