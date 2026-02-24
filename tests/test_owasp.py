import pytest
from crowe_codex.core.agent import Agent, AgentConfig
from crowe_codex.security.owasp import (
    OWASPScanner,
    OWASPFinding,
    OWASPReport,
    OWASP_TOP_10,
)


class FakeAgent(Agent):
    def __init__(self, response: str):
        super().__init__(config=AgentConfig(name="fake", provider="test"))
        self._response = response

    async def execute(self, prompt, context=None):
        return self._response

    async def is_available(self):
        return True


def test_owasp_top_10_has_10_entries():
    assert len(OWASP_TOP_10) == 10


def test_owasp_finding_cross_validated():
    f = OWASPFinding(
        category="Injection", category_id="A03",
        description="SQL injection", severity="high",
        agent_name="claude", confirmed_by=["codex"],
    )
    assert f.cross_validated


def test_owasp_finding_not_cross_validated():
    f = OWASPFinding(
        category="Injection", category_id="A03",
        description="SQL injection", severity="high",
        agent_name="claude",
    )
    assert not f.cross_validated


def test_owasp_report_clean():
    report = OWASPReport(findings=[], agents_used=["claude", "codex"])
    assert report.is_clean
    assert report.vulnerability_count == 0


def test_owasp_report_with_findings():
    findings = [
        OWASPFinding(
            category="Injection", category_id="A03",
            description="XSS found", severity="high",
            agent_name="claude", confirmed_by=["codex"],
        ),
    ]
    report = OWASPReport(findings=findings, agents_used=["claude", "codex"])
    assert not report.is_clean
    assert report.vulnerability_count == 1


def test_owasp_report_unconfirmed_high_still_clean():
    """High severity finding not cross-validated doesn't fail."""
    findings = [
        OWASPFinding(
            category="Injection", category_id="A03",
            description="maybe", severity="high",
            agent_name="claude",
        ),
    ]
    report = OWASPReport(findings=findings, agents_used=["claude"])
    assert report.is_clean


@pytest.mark.asyncio
async def test_owasp_scanner_clean_code():
    agents = {
        "claude": FakeAgent("NO_VULNERABILITIES_FOUND"),
        "codex": FakeAgent("NO_VULNERABILITIES_FOUND"),
    }
    scanner = OWASPScanner(agents)
    report = await scanner.scan("def hello(): return 'world'")
    assert report.is_clean
    assert len(report.agents_used) == 2


@pytest.mark.asyncio
async def test_owasp_scanner_finds_issues():
    agents = {
        "claude": FakeAgent("[A03] HIGH: SQL injection in query builder"),
        "codex": FakeAgent("[A03] HIGH: SQL injection vulnerability detected"),
    }
    scanner = OWASPScanner(agents)
    report = await scanner.scan("query = f'SELECT * FROM users WHERE id={user_id}'")
    assert len(report.findings) >= 2
    # Both agents found A03, so should be cross-validated
    a03_findings = [f for f in report.findings if f.category_id == "A03"]
    assert any(f.cross_validated for f in a03_findings)


@pytest.mark.asyncio
async def test_owasp_scanner_excludes_dispatch():
    agents = {
        "claude": FakeAgent("NO_VULNERABILITIES_FOUND"),
        "dispatch": FakeAgent("should not be called"),
    }
    scanner = OWASPScanner(agents)
    report = await scanner.scan("clean code")
    assert "dispatch" not in report.agents_used


def test_owasp_report_summary():
    report = OWASPReport(
        findings=[],
        agents_used=["claude", "codex"],
        categories_scanned=list(OWASP_TOP_10.keys()),
    )
    assert "CLEAN" in report.summary
