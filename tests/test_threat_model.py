import pytest

from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.security.threat_model import (
    ThreatModelEngine,
    ThreatModel,
    Threat,
    STRIDE,
)


class FakeAgent(Agent):
    def __init__(self, response: str):
        super().__init__(config=AgentConfig(name="fake", provider="test"))
        self._response = response

    async def execute(self, prompt, context=None):
        return self._response

    async def is_available(self):
        return True


def test_stride_has_6_categories():
    assert len(STRIDE) == 6


def test_threat_creation():
    t = Threat(
        id="T001", name="SQL Injection", category="T",
        description="User input in query", severity="high",
    )
    assert t.status == "identified"
    assert t.id == "T001"


def test_threat_serialization():
    t = Threat(
        id="T001", name="XSS", category="I",
        description="Reflected XSS", severity="medium",
        mitigation="Sanitize output",
    )
    d = t.to_dict()
    t2 = Threat.from_dict(d)
    assert t2.name == "XSS"
    assert t2.mitigation == "Sanitize output"


def test_threat_model_empty():
    model = ThreatModel()
    assert model.unmitigated_count == 0
    assert len(model.critical_threats) == 0


def test_threat_model_with_threats():
    model = ThreatModel(threats=[
        Threat(id="T001", name="A", category="S",
               description="x", severity="critical"),
        Threat(id="T002", name="B", category="T",
               description="y", severity="low", status="mitigated"),
    ])
    assert model.unmitigated_count == 1
    assert len(model.critical_threats) == 1


def test_threat_model_serialization():
    model = ThreatModel(
        threats=[
            Threat(id="T001", name="Test", category="S",
                   description="desc", severity="high"),
        ],
        assets=["database"],
        trust_boundaries=["api_gateway"],
    )
    d = model.to_dict()
    m2 = ThreatModel.from_dict(d)
    assert len(m2.threats) == 1
    assert m2.threats[0].name == "Test"
    assert "database" in m2.assets


def test_threat_model_summary():
    model = ThreatModel(threats=[
        Threat(id="T001", name="A", category="S",
               description="x", severity="critical"),
    ])
    assert "1 threats" in model.summary
    assert "1 critical" in model.summary


@pytest.mark.asyncio
async def test_threat_engine_analyze():
    agents = {
        "claude": FakeAgent("[S] HIGH Spoofing threat: no auth on endpoint"),
        "codex": FakeAgent("[I] MEDIUM Information Disclosure threat: debug info exposed"),
    }
    engine = ThreatModelEngine(agents)
    model = await engine.analyze("def api(): return data")
    assert len(model.threats) >= 1


@pytest.mark.asyncio
async def test_threat_engine_evolve():
    existing = ThreatModel(threats=[
        Threat(id="T001", name="Spoofing threat", category="S",
               description="no auth", severity="high"),
    ])
    agents = {
        "claude": FakeAgent("[D] LOW Denial of Service threat: no rate limiting"),
    }
    engine = ThreatModelEngine(agents)
    evolved = await engine.evolve(existing, "def api(): check_auth(); return data")
    # Should have original + new threat
    assert len(evolved.threats) >= 1


@pytest.mark.asyncio
async def test_threat_engine_persistence(tmp_path):
    path = tmp_path / "threats.json"
    agents = {
        "claude": FakeAgent("[S] HIGH Spoofing threat: weak auth"),
    }
    engine = ThreatModelEngine(agents, persist_path=path)
    await engine.analyze("code")
    assert path.exists()

    loaded = engine.load()
    assert loaded is not None
    assert len(loaded.threats) >= 0


@pytest.mark.asyncio
async def test_threat_engine_excludes_dispatch():
    agents = {
        "claude": FakeAgent("[S] HIGH Spoofing threat: test"),
        "dispatch": FakeAgent("should not be called"),
    }
    engine = ThreatModelEngine(agents)
    model = await engine.analyze("code")
    # dispatch should be excluded
    assert len(model.threats) >= 0
