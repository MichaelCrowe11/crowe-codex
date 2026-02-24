"""Compliance mapping: SOC2, HIPAA, PCI-DSS framework verification."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from crowe_codex.core.agent import Agent


# Compliance frameworks and their key controls
FRAMEWORKS: dict[str, dict[str, str]] = {
    "soc2": {
        "CC6.1": "Logical and physical access controls",
        "CC6.2": "Prior to issuing system credentials, registration/authorization",
        "CC6.3": "Role-based access control",
        "CC6.6": "Measures against threats outside system boundaries",
        "CC6.7": "Restrict transmission/movement of data to authorized users",
        "CC6.8": "Prevent/detect unauthorized software",
        "CC7.1": "Monitoring for security events",
        "CC7.2": "Monitor system components for anomalies",
        "CC8.1": "Change management processes",
    },
    "hipaa": {
        "164.312(a)(1)": "Access control — unique user identification",
        "164.312(a)(2)(iv)": "Encryption and decryption",
        "164.312(b)": "Audit controls",
        "164.312(c)(1)": "Integrity — protect ePHI from improper alteration",
        "164.312(d)": "Person or entity authentication",
        "164.312(e)(1)": "Transmission security",
        "164.308(a)(1)": "Security management process",
        "164.308(a)(5)": "Security awareness and training",
    },
    "pci_dss": {
        "Req 2": "Do not use vendor-supplied defaults",
        "Req 3": "Protect stored cardholder data",
        "Req 4": "Encrypt transmission of cardholder data",
        "Req 6": "Develop and maintain secure systems",
        "Req 7": "Restrict access by business need to know",
        "Req 8": "Identify and authenticate access",
        "Req 10": "Track and monitor all access",
        "Req 11": "Regularly test security systems",
    },
}


@dataclass
class ComplianceCheck:
    """A single compliance control check result."""

    framework: str
    control_id: str
    control_name: str
    status: str  # pass, fail, partial, not_applicable
    evidence: str = ""
    recommendation: str = ""


@dataclass
class ComplianceReport:
    """Complete compliance assessment report."""

    checks: list[ComplianceCheck] = field(default_factory=list)
    frameworks_assessed: list[str] = field(default_factory=list)
    agents_used: list[str] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        applicable = [c for c in self.checks if c.status != "not_applicable"]
        if not applicable:
            return 1.0
        passed = [c for c in applicable if c.status == "pass"]
        return len(passed) / len(applicable)

    @property
    def failing_checks(self) -> list[ComplianceCheck]:
        return [c for c in self.checks if c.status == "fail"]

    @property
    def summary(self) -> str:
        total = len(self.checks)
        passed = len([c for c in self.checks if c.status == "pass"])
        failed = len(self.failing_checks)
        return (
            f"Compliance: {passed}/{total} passed, {failed} failed, "
            f"{self.pass_rate:.0%} pass rate"
        )

    def framework_results(self) -> dict[str, bool]:
        """Returns pass/fail per framework."""
        results: dict[str, bool] = {}
        for framework in self.frameworks_assessed:
            fw_checks = [c for c in self.checks if c.framework == framework]
            fw_fails = [c for c in fw_checks if c.status == "fail"]
            results[framework] = len(fw_fails) == 0
        return results


class ComplianceMapper:
    """Maps code against compliance frameworks using cross-vendor verification."""

    def __init__(self, agents: dict[str, Agent]) -> None:
        self._agents = {k: v for k, v in agents.items() if k != "dispatch"}

    async def assess(
        self,
        code: str,
        frameworks: list[str] | None = None,
        context: str = "",
    ) -> ComplianceReport:
        """Assess code against specified compliance frameworks."""
        target_frameworks = frameworks or list(FRAMEWORKS.keys())
        target_frameworks = [
            f for f in target_frameworks if f in FRAMEWORKS
        ]

        all_checks: list[ComplianceCheck] = []

        for framework in target_frameworks:
            prompt = self._build_assessment_prompt(
                code, framework, context
            )

            tasks = {
                name: agent.execute(prompt)
                for name, agent in self._agents.items()
            }
            results = dict(
                zip(tasks.keys(), await asyncio.gather(*tasks.values()))
            )

            checks = self._merge_assessments(framework, results)
            all_checks.extend(checks)

        return ComplianceReport(
            checks=all_checks,
            frameworks_assessed=target_frameworks,
            agents_used=list(self._agents.keys()),
        )

    def _build_assessment_prompt(
        self, code: str, framework: str, context: str
    ) -> str:
        controls = FRAMEWORKS[framework]
        controls_text = "\n".join(
            f"- {cid}: {name}" for cid, name in controls.items()
        )
        return (
            f"Assess this code against {framework.upper()} compliance controls.\n\n"
            f"Code:\n```\n{code}\n```\n\n"
            f"{'Context: ' + context + chr(10) + chr(10) if context else ''}"
            f"Controls to check:\n{controls_text}\n\n"
            "For each control, report:\n"
            "- Control ID\n"
            "- Status: PASS, FAIL, PARTIAL, or NOT_APPLICABLE\n"
            "- Evidence or reasoning\n"
            "- Recommendation if failing\n\n"
            "Format: CONTROL_ID: STATUS - evidence | RECOMMENDATION: suggestion"
        )

    def _merge_assessments(
        self,
        framework: str,
        results: dict[str, str],
    ) -> list[ComplianceCheck]:
        """Merge multiple agent assessments for a framework."""
        controls = FRAMEWORKS[framework]
        check_votes: dict[str, list[str]] = {
            cid: [] for cid in controls
        }

        for response in results.values():
            for cid in controls:
                if cid in response:
                    status = "pass"
                    response_upper = response.upper()
                    idx = response_upper.find(cid)
                    if idx >= 0:
                        context_str = response_upper[idx:idx + 200]
                        if "FAIL" in context_str:
                            status = "fail"
                        elif "PARTIAL" in context_str:
                            status = "partial"
                        elif "NOT_APPLICABLE" in context_str or "N/A" in context_str:
                            status = "not_applicable"
                    check_votes[cid].append(status)

        checks = []
        for cid, name in controls.items():
            votes = check_votes[cid]
            if not votes:
                status = "not_applicable"
            elif "fail" in votes:
                # Conservative: if any agent says fail, it's fail
                status = "fail"
            elif "partial" in votes:
                status = "partial"
            else:
                status = "pass"

            checks.append(ComplianceCheck(
                framework=framework,
                control_id=cid,
                control_name=name,
                status=status,
            ))

        return checks
