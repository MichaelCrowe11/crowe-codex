from crowe_codex.core.result import (
    AgentOutput,
    ConfidenceReport,
    PipelineResult,
    SecurityAttestation,
    Stage,
)


def test_stage_enum_has_all_stages():
    assert Stage.ARCHITECT.value == 1
    assert Stage.BUILDER.value == 2
    assert Stage.SPECIALIST.value == 3
    assert Stage.ACCELERATOR.value == 4
    assert Stage.DISPATCH.value == 5


def test_agent_output_creation():
    output = AgentOutput(
        stage=Stage.ARCHITECT,
        agent_name="claude",
        content="plan: build a rate limiter",
        metadata={"model": "claude-opus-4-6"},
    )
    assert output.stage == Stage.ARCHITECT
    assert output.agent_name == "claude"


def test_security_attestation_defaults():
    att = SecurityAttestation()
    assert att.owasp_clean is False
    assert att.dependencies_verified is False
    assert att.supply_chain_risks == 0
    assert att.vulnerabilities_found == 0
    assert att.attacks_survived == 0


def test_confidence_report_high_score():
    report = ConfidenceReport(
        architecture_preserved=True,
        tests_passing=True,
        vulnerabilities_found=0,
        dependencies_verified=True,
        owasp_clean=True,
        models_consulted=3,
        cross_vendor_agreement=1.0,
    )
    assert report.score >= 90


def test_confidence_report_low_score():
    report = ConfidenceReport(
        architecture_preserved=False,
        tests_passing=False,
        vulnerabilities_found=5,
        dependencies_verified=False,
        owasp_clean=False,
        models_consulted=1,
        cross_vendor_agreement=0.3,
    )
    assert report.score < 50


def test_pipeline_result_creation():
    result = PipelineResult(
        code="def rate_limit(): pass",
        stage_outputs=[],
        confidence=ConfidenceReport(
            architecture_preserved=True,
            tests_passing=True,
            vulnerabilities_found=0,
            dependencies_verified=True,
            owasp_clean=True,
            models_consulted=3,
            cross_vendor_agreement=1.0,
        ),
        security=SecurityAttestation(),
    )
    assert result.code == "def rate_limit(): pass"
    assert result.confidence.score >= 90
