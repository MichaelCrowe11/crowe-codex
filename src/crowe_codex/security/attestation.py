"""Security attestation generator: produces signed security reports."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from crowe_codex.security.owasp import OWASPReport
from crowe_codex.security.supply_chain import SupplyChainReport
from crowe_codex.security.threat_model import ThreatModel
from crowe_codex.security.compliance import ComplianceReport


@dataclass
class AttestationMetadata:
    """Metadata about the attestation process."""

    timestamp: str = ""
    crowe_codex_version: str = ""
    agents_used: list[str] = field(default_factory=list)
    code_hash: str = ""
    strategy_used: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class SecurityAttestation:
    """Complete security attestation with all verification results."""

    metadata: AttestationMetadata
    owasp: OWASPReport | None = None
    supply_chain: SupplyChainReport | None = None
    threat_model: ThreatModel | None = None
    compliance: ComplianceReport | None = None

    @property
    def overall_score(self) -> int:
        """Calculate overall security score 0-100."""
        score = 0
        checks = 0

        if self.owasp is not None:
            checks += 1
            if self.owasp.is_clean:
                score += 25
            else:
                # Partial credit for few findings
                max_penalty = min(self.owasp.vulnerability_count * 5, 25)
                score += max(25 - max_penalty, 0)

        if self.supply_chain is not None:
            checks += 1
            if self.supply_chain.is_safe:
                score += 25
            else:
                ratio = self.supply_chain.verified_count / max(self.supply_chain.total_deps, 1)
                score += int(25 * ratio)

        if self.threat_model is not None:
            checks += 1
            if not self.threat_model.critical_threats:
                score += 25
            else:
                # Partial credit based on mitigation
                total = len(self.threat_model.threats)
                mitigated = len([
                    t for t in self.threat_model.threats
                    if t.status == "mitigated"
                ])
                ratio = mitigated / max(total, 1)
                score += int(25 * ratio)

        if self.compliance is not None:
            checks += 1
            score += int(25 * self.compliance.pass_rate)

        if checks == 0:
            return 0

        # Scale to 100 based on checks performed
        return min(int(score * (4 / checks)), 100)

    @property
    def verdict(self) -> str:
        """Human-readable security verdict."""
        score = self.overall_score
        if score >= 90:
            return "STRONG"
        elif score >= 70:
            return "ACCEPTABLE"
        elif score >= 50:
            return "NEEDS_IMPROVEMENT"
        else:
            return "CRITICAL_ISSUES"

    @property
    def summary(self) -> str:
        parts = [f"Security Attestation: {self.verdict} ({self.overall_score}/100)"]
        if self.owasp:
            parts.append(self.owasp.summary)
        if self.supply_chain:
            parts.append(self.supply_chain.summary)
        if self.threat_model:
            parts.append(self.threat_model.summary)
        if self.compliance:
            parts.append(self.compliance.summary)
        return "\n".join(parts)

    def to_dict(self) -> dict:
        result: dict = {
            "metadata": {
                "timestamp": self.metadata.timestamp,
                "crowe_codex_version": self.metadata.crowe_codex_version,
                "agents_used": self.metadata.agents_used,
                "code_hash": self.metadata.code_hash,
                "strategy_used": self.metadata.strategy_used,
            },
            "overall_score": self.overall_score,
            "verdict": self.verdict,
        }
        if self.owasp:
            result["owasp"] = {
                "clean": self.owasp.is_clean,
                "findings": self.owasp.vulnerability_count,
            }
        if self.supply_chain:
            result["supply_chain"] = {
                "safe": self.supply_chain.is_safe,
                "verified": self.supply_chain.verified_count,
                "total": self.supply_chain.total_deps,
                "risks": self.supply_chain.risk_count,
            }
        if self.threat_model:
            result["threat_model"] = {
                "total_threats": len(self.threat_model.threats),
                "critical": len(self.threat_model.critical_threats),
                "unmitigated": self.threat_model.unmitigated_count,
            }
        if self.compliance:
            result["compliance"] = {
                "pass_rate": self.compliance.pass_rate,
                "frameworks": self.compliance.framework_results(),
            }
        return result

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class AttestationGenerator:
    """Generates security attestations by orchestrating all security modules."""

    def __init__(self, version: str = "2.0.0") -> None:
        self._version = version

    def generate(
        self,
        code: str,
        owasp: OWASPReport | None = None,
        supply_chain: SupplyChainReport | None = None,
        threat_model: ThreatModel | None = None,
        compliance: ComplianceReport | None = None,
        agents_used: list[str] | None = None,
        strategy: str = "",
    ) -> SecurityAttestation:
        """Generate a complete security attestation."""
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]

        metadata = AttestationMetadata(
            crowe_codex_version=self._version,
            agents_used=agents_used or [],
            code_hash=code_hash,
            strategy_used=strategy,
        )

        return SecurityAttestation(
            metadata=metadata,
            owasp=owasp,
            supply_chain=supply_chain,
            threat_model=threat_model,
            compliance=compliance,
        )
