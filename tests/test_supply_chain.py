import pytest
from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.security.supply_chain import (
    SupplyChainVerifier,
    SupplyChainReport,
    DependencyInfo,
    detect_slopsquatting,
)


class FakeAgent(Agent):
    def __init__(self, response: str):
        super().__init__(config=AgentConfig(name="fake", provider="test"))
        self._response = response

    async def execute(self, prompt, context=None):
        return self._response

    async def is_available(self):
        return True


def test_detect_slopsquatting_clean():
    assert detect_slopsquatting("requests") == []
    assert detect_slopsquatting("flask") == []
    assert detect_slopsquatting("numpy") == []


def test_detect_slopsquatting_typo():
    warnings = detect_slopsquatting("requets")
    assert len(warnings) > 0
    assert any("typosquat" in w for w in warnings)


def test_detect_slopsquatting_repeated_chars():
    warnings = detect_slopsquatting("flaaaaaask")
    assert len(warnings) > 0


def test_detect_slopsquatting_known_safe():
    assert detect_slopsquatting("python-dateutil") == []
    assert detect_slopsquatting("python-dotenv") == []


def test_detect_slopsquatting_python_prefix():
    warnings = detect_slopsquatting("python-fakepackage")
    assert len(warnings) > 0


def test_dependency_info_defaults():
    dep = DependencyInfo(name="requests")
    assert dep.verified is False
    assert dep.risk_level == "unknown"


def test_supply_chain_report_safe():
    report = SupplyChainReport(
        dependencies=[
            DependencyInfo(name="requests", verified=True, risk_level="safe"),
        ],
        agents_used=["claude"],
    )
    assert report.is_safe
    assert report.verified_count == 1
    assert report.risk_count == 0


def test_supply_chain_report_risky():
    report = SupplyChainReport(
        dependencies=[
            DependencyInfo(name="requets", risk_level="high"),
        ],
        agents_used=["claude"],
        slopsquatting_suspects=["requets"],
    )
    assert not report.is_safe
    assert report.risk_count == 1


@pytest.mark.asyncio
async def test_verifier_basic():
    agents = {
        "claude": FakeAgent("requests: SAFE - well-known HTTP library"),
        "codex": FakeAgent("requests: SAFE - popular package"),
    }
    verifier = SupplyChainVerifier(agents)
    report = await verifier.verify(["requests>=2.28.0"])
    assert report.total_deps == 1
    assert report.dependencies[0].name == "requests"
    assert len(report.agents_used) == 2


@pytest.mark.asyncio
async def test_verifier_detects_suspect():
    agents = {
        "claude": FakeAgent("requets: HIGH_RISK - typosquat of requests"),
    }
    verifier = SupplyChainVerifier(agents)
    report = await verifier.verify(["requets>=1.0"])
    assert "requets" in report.slopsquatting_suspects


@pytest.mark.asyncio
async def test_verifier_parses_version():
    agents = {
        "claude": FakeAgent("flask: SAFE"),
    }
    verifier = SupplyChainVerifier(agents)
    report = await verifier.verify(["flask>=2.0.0", "click==8.1.0"])
    assert report.dependencies[0].version == "2.0.0"
    assert report.dependencies[1].version == "8.1.0"


def test_supply_chain_report_summary():
    report = SupplyChainReport(
        dependencies=[
            DependencyInfo(name="a", verified=True, risk_level="safe"),
            DependencyInfo(name="b", verified=False, risk_level="unknown"),
        ],
        agents_used=["claude"],
    )
    assert "1/2 verified" in report.summary
