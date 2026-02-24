import json

from crowe_codex.security.attestation import (
    AttestationGenerator,
    AttestationMetadata,
)
from crowe_codex.security.owasp import OWASPReport, OWASPFinding
from crowe_codex.security.supply_chain import SupplyChainReport, DependencyInfo
from crowe_codex.security.threat_model import ThreatModel
from crowe_codex.security.compliance import ComplianceReport, ComplianceCheck


def test_attestation_metadata_auto_timestamp():
    meta = AttestationMetadata()
    assert meta.timestamp != ""


def test_attestation_generator_basic():
    gen = AttestationGenerator(version="0.5.0")
    att = gen.generate(code="def hello(): pass", agents_used=["claude"])
    assert att.metadata.crowe_codex_version == "0.5.0"
    assert len(att.metadata.code_hash) == 16


def test_attestation_score_all_clean():
    owasp = OWASPReport(findings=[], agents_used=["claude"])
    supply = SupplyChainReport(
        dependencies=[DependencyInfo(name="x", verified=True, risk_level="safe")],
        agents_used=["claude"],
    )
    threats = ThreatModel(threats=[])
    compliance = ComplianceReport(
        checks=[ComplianceCheck(framework="soc2", control_id="CC6.1",
                               control_name="test", status="pass")],
        frameworks_assessed=["soc2"],
    )
    gen = AttestationGenerator()
    att = gen.generate(
        code="safe code",
        owasp=owasp,
        supply_chain=supply,
        threat_model=threats,
        compliance=compliance,
    )
    assert att.overall_score == 100
    assert att.verdict == "STRONG"


def test_attestation_score_partial():
    owasp = OWASPReport(
        findings=[
            OWASPFinding(
                category="Injection", category_id="A03",
                description="XSS", severity="high",
                agent_name="claude", confirmed_by=["codex"],
            ),
        ],
        agents_used=["claude", "codex"],
    )
    gen = AttestationGenerator()
    att = gen.generate(code="risky", owasp=owasp)
    assert att.overall_score < 100


def test_attestation_score_no_checks():
    gen = AttestationGenerator()
    att = gen.generate(code="code")
    assert att.overall_score == 0


def test_attestation_verdict_needs_improvement():
    owasp = OWASPReport(
        findings=[
            OWASPFinding(
                category="Injection", category_id="A03",
                description="SQL injection", severity="critical",
                agent_name="claude", confirmed_by=["codex", "ollama"],
            ),
            OWASPFinding(
                category="XSS", category_id="A03",
                description="Reflected XSS", severity="high",
                agent_name="codex", confirmed_by=["claude"],
            ),
        ],
        agents_used=["claude", "codex"],
    )
    gen = AttestationGenerator()
    att = gen.generate(code="bad code", owasp=owasp)
    assert att.verdict in ("NEEDS_IMPROVEMENT", "CRITICAL_ISSUES")


def test_attestation_to_json():
    owasp = OWASPReport(findings=[], agents_used=["claude"])
    gen = AttestationGenerator()
    att = gen.generate(code="code", owasp=owasp)
    j = att.to_json()
    parsed = json.loads(j)
    assert "overall_score" in parsed
    assert "verdict" in parsed
    assert "owasp" in parsed


def test_attestation_to_dict_complete():
    gen = AttestationGenerator()
    att = gen.generate(
        code="code",
        owasp=OWASPReport(findings=[], agents_used=["c"]),
        supply_chain=SupplyChainReport(
            dependencies=[DependencyInfo(name="x", verified=True, risk_level="safe")],
            agents_used=["c"],
        ),
        threat_model=ThreatModel(threats=[]),
        compliance=ComplianceReport(
            checks=[ComplianceCheck(framework="soc2", control_id="CC6.1",
                                   control_name="test", status="pass")],
            frameworks_assessed=["soc2"],
        ),
    )
    d = att.to_dict()
    assert "owasp" in d
    assert "supply_chain" in d
    assert "threat_model" in d
    assert "compliance" in d


def test_attestation_summary():
    owasp = OWASPReport(findings=[], agents_used=["claude"])
    gen = AttestationGenerator()
    att = gen.generate(code="code", owasp=owasp, strategy="adversarial")
    assert "STRONG" in att.summary or att.verdict in att.summary
    assert att.metadata.strategy_used == "adversarial"
