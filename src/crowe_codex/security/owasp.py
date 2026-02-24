"""OWASP Top 10 sweep using cross-vendor AI verification."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from crowe_codex.core.agent import Agent


OWASP_TOP_10 = {
    "A01": "Broken Access Control",
    "A02": "Cryptographic Failures",
    "A03": "Injection",
    "A04": "Insecure Design",
    "A05": "Security Misconfiguration",
    "A06": "Vulnerable and Outdated Components",
    "A07": "Identification and Authentication Failures",
    "A08": "Software and Data Integrity Failures",
    "A09": "Security Logging and Monitoring Failures",
    "A10": "Server-Side Request Forgery (SSRF)",
}


@dataclass
class OWASPFinding:
    """A single OWASP vulnerability finding."""

    category: str
    category_id: str
    description: str
    severity: str  # critical, high, medium, low, info
    agent_name: str
    confirmed_by: list[str] = field(default_factory=list)

    @property
    def cross_validated(self) -> bool:
        return len(self.confirmed_by) >= 1


@dataclass
class OWASPReport:
    """Complete OWASP scan report."""

    findings: list[OWASPFinding] = field(default_factory=list)
    agents_used: list[str] = field(default_factory=list)
    categories_scanned: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        critical_or_high = [
            f for f in self.findings
            if f.severity in ("critical", "high") and f.cross_validated
        ]
        return len(critical_or_high) == 0

    @property
    def vulnerability_count(self) -> int:
        return len([f for f in self.findings if f.cross_validated])

    @property
    def summary(self) -> str:
        total = len(self.findings)
        confirmed = self.vulnerability_count
        return (
            f"OWASP Scan: {total} findings, {confirmed} cross-validated, "
            f"{'CLEAN' if self.is_clean else 'ISSUES FOUND'}"
        )


class OWASPScanner:
    """Cross-vendor OWASP Top 10 vulnerability scanner."""

    def __init__(self, agents: dict[str, Agent]) -> None:
        self._agents = {k: v for k, v in agents.items() if k != "dispatch"}

    async def scan(self, code: str, context: str = "") -> OWASPReport:
        """Run OWASP Top 10 scan across all available agents."""
        scan_tasks = {}
        for name, agent in self._agents.items():
            prompt = self._build_scan_prompt(code, context)
            scan_tasks[name] = agent.execute(prompt)

        results = dict(
            zip(scan_tasks.keys(), await asyncio.gather(*scan_tasks.values()))
        )

        findings = []
        for agent_name, response in results.items():
            agent_findings = self._parse_findings(response, agent_name)
            findings.extend(agent_findings)

        # Cross-validate: mark findings confirmed by multiple agents
        self._cross_validate(findings)

        return OWASPReport(
            findings=findings,
            agents_used=list(results.keys()),
            categories_scanned=list(OWASP_TOP_10.keys()),
        )

    def _build_scan_prompt(self, code: str, context: str) -> str:
        categories = "\n".join(
            f"- {cid}: {name}" for cid, name in OWASP_TOP_10.items()
        )
        return (
            "You are a security auditor. Analyze this code for OWASP Top 10 "
            "vulnerabilities.\n\n"
            f"Code:\n```\n{code}\n```\n\n"
            f"{'Context: ' + context + chr(10) + chr(10) if context else ''}"
            f"OWASP Top 10 Categories:\n{categories}\n\n"
            "For each vulnerability found, report:\n"
            "- Category ID (A01-A10)\n"
            "- Description of the issue\n"
            "- Severity (critical/high/medium/low/info)\n\n"
            "If the code is clean, respond with: NO_VULNERABILITIES_FOUND\n"
            "Format each finding as: [CATEGORY_ID] SEVERITY: description"
        )

    def _parse_findings(
        self, response: str, agent_name: str
    ) -> list[OWASPFinding]:
        """Parse agent response into structured findings."""
        if "NO_VULNERABILITIES_FOUND" in response:
            return []

        findings = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Try to parse [A01] HIGH: description format
            for cid in OWASP_TOP_10:
                if cid in line:
                    severity = "medium"  # default
                    for sev in ("critical", "high", "medium", "low", "info"):
                        if sev.upper() in line.upper():
                            severity = sev
                            break

                    description = line
                    # Strip the category prefix if present
                    for prefix in (f"[{cid}]", f"{cid}:", f"{cid} "):
                        if description.startswith(prefix):
                            description = description[len(prefix):].strip()

                    findings.append(OWASPFinding(
                        category=OWASP_TOP_10[cid],
                        category_id=cid,
                        description=description,
                        severity=severity,
                        agent_name=agent_name,
                    ))
                    break

        return findings

    def _cross_validate(self, findings: list[OWASPFinding]) -> None:
        """Mark findings that are confirmed by multiple agents."""
        # Group by category
        by_category: dict[str, list[OWASPFinding]] = {}
        for f in findings:
            by_category.setdefault(f.category_id, []).append(f)

        # If multiple agents found the same category, cross-validate
        for cid, category_findings in by_category.items():
            agents = {f.agent_name for f in category_findings}
            if len(agents) >= 2:
                for f in category_findings:
                    f.confirmed_by = [a for a in agents if a != f.agent_name]
