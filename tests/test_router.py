import pytest
from pathlib import Path

from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.strategies.router import (
    AdaptiveRouter,
    RoutingHistory,
)
from crowe_codex.strategies.consensus import Consensus
from crowe_codex.strategies.adversarial import Adversarial


class FakeAgent(Agent):
    def __init__(self, response: str):
        super().__init__(config=AgentConfig(name="fake", provider="test"))
        self._response = response

    async def execute(self, prompt, context=None):
        return self._response

    async def is_available(self):
        return True


def test_routing_history_in_memory(tmp_path):
    history = RoutingHistory(path=tmp_path / "history.json")
    history.record("fix security vulnerability", "adversarial", 85.0)
    assert history.best_strategy_for("security audit") == "adversarial"


def test_routing_history_persistence(tmp_path):
    path = tmp_path / "history.json"
    h1 = RoutingHistory(path=path)
    h1.record("optimize performance", "evolutionary", 90.0)

    h2 = RoutingHistory(path=path)
    assert h2.best_strategy_for("performance tuning") == "evolutionary"


def test_routing_history_no_match(tmp_path):
    history = RoutingHistory(path=tmp_path / "history.json")
    history.record("security task", "adversarial", 80.0)
    assert history.best_strategy_for("something completely different") is None


def test_routing_history_best_by_score(tmp_path):
    history = RoutingHistory(path=tmp_path / "history.json")
    history.record("test something", "verification_loop", 90.0)
    history.record("test something", "consensus", 60.0)
    assert history.best_strategy_for("write tests") == "verification_loop"


def test_router_keyword_routing():
    router = AdaptiveRouter(
        strategies={
            "adversarial": Adversarial(),
            "consensus": Consensus(),
        },
        history=RoutingHistory(path=Path("/tmp/test_router_kw.json")),
    )
    selected = router.select_strategy("fix XSS security vulnerability")
    assert selected.name == "adversarial"


def test_router_defaults_to_consensus():
    router = AdaptiveRouter(
        strategies={
            "adversarial": Adversarial(),
            "consensus": Consensus(),
        },
        history=RoutingHistory(path=Path("/tmp/test_router_default.json")),
    )
    selected = router.select_strategy("do something random")
    assert selected.name == "consensus"


def test_router_learned_overrides_keyword(tmp_path):
    path = tmp_path / "history.json"
    history = RoutingHistory(path=path)
    # Record that consensus worked great for security tasks (unusual)
    history.record("security fix", "consensus", 95.0)

    router = AdaptiveRouter(
        strategies={
            "adversarial": Adversarial(),
            "consensus": Consensus(),
        },
        history=history,
    )
    # Learned history should override keyword-based routing
    selected = router.select_strategy("security audit")
    assert selected.name == "consensus"


@pytest.mark.asyncio
async def test_router_execute_delegates():
    agents = {
        "claude": FakeAgent("claude output"),
        "codex": FakeAgent("codex output"),
        "dispatch": FakeAgent("merged"),
    }
    router = AdaptiveRouter(
        strategies={"consensus": Consensus()},
        history=RoutingHistory(path=Path("/tmp/test_router_exec.json")),
    )
    result = await router.execute("build something", agents)
    assert result["strategy"] == "adaptive_router"
    assert result["routed_to"] == "consensus"


def test_router_register_strategy():
    router = AdaptiveRouter(strategies={})
    router.register_strategy(Consensus())
    router.register_strategy(Adversarial())
    selected = router.select_strategy("anything")
    assert selected.name == "consensus"  # default fallback
