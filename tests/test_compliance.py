import pytest
from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.security.compliance import (
    ComplianceMapper,
    ComplianceCheck,
    ComplianceReport,
    FRAMEWORKS,
)


class FakeAgent(Agent):
    def __init__(self, response: str):
        super().__init__(config=AgentConfig(name="fake", provider="test"))
        self._response = response

    async def execute(self, prompt, context=None):
        return self._response

    async def is_available(self):
        return True


def test_frameworks_defined():
    assert "soc2" in FRAMEWORKS
    assert "hipaa" in FRAMEWORKS
    assert "pci_dss" in FRAMEWORKS


def test_compliance_check_creation():
    check = ComplianceCheck(
        framework="soc2", control_id="CC6.1",
        control_name="Logical and physical access controls",
        status="pass",
    )
    assert check.status == "pass"


def test_compliance_report_pass_rate():
    checks = [
        ComplianceCheck(framework="soc2", control_id="CC6.1",
                       control_name="test", status="pass"),
        ComplianceCheck(framework="soc2", control_id="CC6.2",
                       control_name="test", status="pass"),
        ComplianceCheck(framework="soc2", control_id="CC6.3",
                       control_name="test", status="fail"),
    ]
    report = ComplianceReport(checks=checks, frameworks_assessed=["soc2"])
    assert abs(report.pass_rate - 2 / 3) < 0.01


def test_compliance_report_all_pass():
    checks = [
        ComplianceCheck(framework="soc2", control_id="CC6.1",
                       control_name="test", status="pass"),
    ]
    report = ComplianceReport(checks=checks, frameworks_assessed=["soc2"])
    assert report.pass_rate == 1.0
    assert len(report.failing_checks) == 0


def test_compliance_report_na_excluded():
    checks = [
        ComplianceCheck(framework="soc2", control_id="CC6.1",
                       control_name="test", status="pass"),
        ComplianceCheck(framework="soc2", control_id="CC6.2",
                       control_name="test", status="not_applicable"),
    ]
    report = ComplianceReport(checks=checks, frameworks_assessed=["soc2"])
    assert report.pass_rate == 1.0  # N/A excluded from calculation


def test_compliance_report_framework_results():
    checks = [
        ComplianceCheck(framework="soc2", control_id="CC6.1",
                       control_name="test", status="pass"),
        ComplianceCheck(framework="hipaa", control_id="164.312(b)",
                       control_name="test", status="fail"),
    ]
    report = ComplianceReport(
        checks=checks,
        frameworks_assessed=["soc2", "hipaa"],
    )
    results = report.framework_results()
    assert results["soc2"] is True
    assert results["hipaa"] is False


def test_compliance_report_summary():
    report = ComplianceReport(
        checks=[
            ComplianceCheck(framework="soc2", control_id="CC6.1",
                           control_name="test", status="pass"),
        ],
        frameworks_assessed=["soc2"],
    )
    assert "1/1 passed" in report.summary


@pytest.mark.asyncio
async def test_compliance_mapper_basic():
    agents = {
        "claude": FakeAgent("CC6.1: PASS - access controls implemented"),
        "codex": FakeAgent("CC6.1: PASS - looks good"),
    }
    mapper = ComplianceMapper(agents)
    report = await mapper.assess("def auth(): check_token()", frameworks=["soc2"])
    assert len(report.checks) > 0
    assert "soc2" in report.frameworks_assessed


@pytest.mark.asyncio
async def test_compliance_mapper_detects_failure():
    agents = {
        "claude": FakeAgent("CC6.1: FAIL - no access control found"),
    }
    mapper = ComplianceMapper(agents)
    report = await mapper.assess("def api(): return data", frameworks=["soc2"])
    cc61 = [c for c in report.checks if c.control_id == "CC6.1"]
    assert len(cc61) > 0
    assert cc61[0].status == "fail"


@pytest.mark.asyncio
async def test_compliance_mapper_multiple_frameworks():
    agents = {
        "claude": FakeAgent("CC6.1: PASS\n164.312(b): PASS\nReq 6: PASS"),
    }
    mapper = ComplianceMapper(agents)
    report = await mapper.assess(
        "secure code",
        frameworks=["soc2", "hipaa", "pci_dss"],
    )
    assert len(report.frameworks_assessed) == 3
