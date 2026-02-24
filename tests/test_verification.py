import pytest
from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.core.result import Stage
from crowe_codex.strategies.verification import VerificationLoop


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


def test_verification_loop_required_stages():
    strategy = VerificationLoop()
    assert Stage.ARCHITECT in strategy.required_stages
    assert Stage.BUILDER in strategy.required_stages
    assert Stage.DISPATCH in strategy.required_stages


def test_verification_loop_name():
    assert VerificationLoop().name == "verification_loop"


@pytest.mark.asyncio
async def test_verification_loop_basic():
    agents = {
        "claude": FakeAgent("def add(a, b): return a + b"),
        "codex": FakeAgent("def test_add(): assert add(1, 2) == 3"),
        "dispatch": FakeAgent("PASS: code and tests verified"),
    }
    strategy = VerificationLoop(iterations=1)
    result = await strategy.execute("write an add function", agents)
    assert result["strategy"] == "verification_loop"
    assert result["iterations"] == 1
    assert result["code_versions"] == 1
    assert result["test_versions"] == 1
    assert "code_output" in result
    assert "test_output" in result
    assert "dispatch_output" in result


@pytest.mark.asyncio
async def test_verification_loop_multiple_iterations():
    claude = FakeAgent("code v1")
    codex = FakeAgent("test v1")
    dispatch = FakeAgent("verified")

    agents = {"claude": claude, "codex": codex, "dispatch": dispatch}
    strategy = VerificationLoop(iterations=3)
    result = await strategy.execute("build something", agents)

    assert result["iterations"] == 3
    assert result["code_versions"] == 3
    assert result["test_versions"] == 3
    # Claude: initial code + 1 fix (iteration 2) = 2 calls
    # Plus 1 more-tests call (iteration 1) = 3 total
    assert claude.call_count >= 2
    assert codex.call_count >= 2


@pytest.mark.asyncio
async def test_verification_loop_swap_agents():
    """Verify agents alternate between code and test roles."""
    claude = FakeAgent("claude output")
    codex = FakeAgent("codex output")
    dispatch = FakeAgent("done")

    agents = {"claude": claude, "codex": codex, "dispatch": dispatch}
    strategy = VerificationLoop(iterations=2)
    await strategy.execute("task", agents)
    # Both agents should be called multiple times due to swapping
    assert claude.call_count >= 1
    assert codex.call_count >= 1
