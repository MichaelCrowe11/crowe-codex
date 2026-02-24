import pytest
from claude_codex.core.agent import Agent, AgentConfig
from claude_codex.core.result import Stage
from claude_codex.strategies.adversarial import Adversarial


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


def test_adversarial_required_stages():
    strategy = Adversarial()
    assert Stage.ARCHITECT in strategy.required_stages
    assert Stage.BUILDER in strategy.required_stages
    assert Stage.SPECIALIST in strategy.required_stages
    assert Stage.DISPATCH in strategy.required_stages


@pytest.mark.asyncio
async def test_adversarial_runs_build_attack_fuzz():
    agents = {
        "claude": FakeAgent("def rate_limit(): pass"),
        "codex": FakeAgent("found XSS vulnerability"),
        "ollama": FakeAgent("edge case: empty input"),
        "dispatch": FakeAgent('{"code": "def rate_limit(): pass", "attacks_survived": 3}'),
    }
    strategy = Adversarial()
    result = await strategy.execute("implement rate limiter", agents)
    assert "build_output" in result
    assert "attack_output" in result
    assert "fuzz_output" in result
    assert result["strategy"] == "adversarial"
    assert result["total_attacks"] == 1


@pytest.mark.asyncio
async def test_adversarial_multiple_rounds():
    builder = FakeAgent("code v1")
    attacker = FakeAgent("found issue: no input validation")
    fuzzer = FakeAgent("edge case: empty string")
    dispatch = FakeAgent("final code")

    agents = {
        "claude": builder,
        "codex": attacker,
        "ollama": fuzzer,
        "dispatch": dispatch,
    }
    strategy = Adversarial(rounds=3)
    result = await strategy.execute("build something", agents)
    # Builder called: initial build + 2 fix rounds = 3
    assert builder.call_count == 3
    assert result["total_attacks"] == 3
    assert result["rounds"] == 3


@pytest.mark.asyncio
async def test_adversarial_single_round_no_fix():
    builder = FakeAgent("code v1")
    agents = {
        "claude": builder,
        "codex": FakeAgent("no issues"),
        "ollama": FakeAgent("no edge cases"),
        "dispatch": FakeAgent("approved"),
    }
    strategy = Adversarial(rounds=1)
    result = await strategy.execute("simple task", agents)
    # Single round: build once, no fix needed
    assert builder.call_count == 1
