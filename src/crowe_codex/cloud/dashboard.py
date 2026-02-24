"""Team Dashboard: aggregated visibility into security and confidence metrics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from crowe_codex.security.attestation import SecurityAttestation


@dataclass
class ProjectSnapshot:
    """A point-in-time snapshot of a project's security posture."""

    project_name: str
    timestamp: str = ""
    security_score: int = 0
    confidence_score: int = 0
    strategy_used: str = ""
    owasp_clean: bool = False
    supply_chain_safe: bool = False
    compliance_pass_rate: float = 0.0
    threats_count: int = 0
    agents_used: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "timestamp": self.timestamp,
            "security_score": self.security_score,
            "confidence_score": self.confidence_score,
            "strategy_used": self.strategy_used,
            "owasp_clean": self.owasp_clean,
            "supply_chain_safe": self.supply_chain_safe,
            "compliance_pass_rate": self.compliance_pass_rate,
            "threats_count": self.threats_count,
            "agents_used": self.agents_used,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ProjectSnapshot:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    @classmethod
    def from_attestation(
        cls,
        project_name: str,
        attestation: SecurityAttestation,
        confidence_score: int = 0,
    ) -> ProjectSnapshot:
        """Create a snapshot from a security attestation."""
        return cls(
            project_name=project_name,
            security_score=attestation.overall_score,
            confidence_score=confidence_score,
            strategy_used=attestation.metadata.strategy_used,
            owasp_clean=attestation.owasp.is_clean if attestation.owasp else False,
            supply_chain_safe=attestation.supply_chain.is_safe if attestation.supply_chain else False,
            compliance_pass_rate=attestation.compliance.pass_rate if attestation.compliance else 0.0,
            threats_count=len(attestation.threat_model.threats) if attestation.threat_model else 0,
            agents_used=attestation.metadata.agents_used,
        )


@dataclass
class TeamDashboard:
    """Aggregated team dashboard across all projects."""

    team_id: str
    snapshots: list[ProjectSnapshot] = field(default_factory=list)

    @property
    def projects(self) -> list[str]:
        """List of unique project names."""
        return sorted({s.project_name for s in self.snapshots})

    @property
    def average_security_score(self) -> float:
        if not self.snapshots:
            return 0.0
        return sum(s.security_score for s in self.snapshots) / len(self.snapshots)

    @property
    def average_confidence_score(self) -> float:
        if not self.snapshots:
            return 0.0
        return sum(s.confidence_score for s in self.snapshots) / len(self.snapshots)

    @property
    def owasp_compliance_rate(self) -> float:
        if not self.snapshots:
            return 0.0
        clean = len([s for s in self.snapshots if s.owasp_clean])
        return clean / len(self.snapshots)

    @property
    def total_runs(self) -> int:
        return len(self.snapshots)

    def latest_snapshot(self, project_name: str) -> ProjectSnapshot | None:
        """Get the most recent snapshot for a project."""
        project_snaps = [s for s in self.snapshots if s.project_name == project_name]
        if not project_snaps:
            return None
        return max(project_snaps, key=lambda s: s.timestamp)

    def project_history(self, project_name: str) -> list[ProjectSnapshot]:
        """Get all snapshots for a project, sorted by time."""
        snaps = [s for s in self.snapshots if s.project_name == project_name]
        return sorted(snaps, key=lambda s: s.timestamp)

    def trend(self, project_name: str) -> str:
        """Calculate security score trend for a project."""
        history = self.project_history(project_name)
        if len(history) < 2:
            return "stable"
        recent = history[-1].security_score
        previous = history[-2].security_score
        if recent > previous:
            return "improving"
        elif recent < previous:
            return "declining"
        return "stable"

    def summary(self) -> dict:
        """Generate a dashboard summary."""
        return {
            "team_id": self.team_id,
            "total_projects": len(self.projects),
            "total_runs": self.total_runs,
            "average_security_score": round(self.average_security_score, 1),
            "average_confidence_score": round(self.average_confidence_score, 1),
            "owasp_compliance_rate": f"{self.owasp_compliance_rate:.0%}",
            "projects": {
                name: {
                    "latest_score": (self.latest_snapshot(name).security_score
                                     if self.latest_snapshot(name) else 0),
                    "trend": self.trend(name),
                    "runs": len(self.project_history(name)),
                }
                for name in self.projects
            },
        }


class DashboardStore:
    """Persists team dashboard data."""

    def __init__(
        self,
        team_id: str = "default",
        persist_path: Path | None = None,
    ) -> None:
        self.team_id = team_id
        self._persist_path = persist_path or (
            Path.home() / ".crowe-codex" / "dashboard" / f"{team_id}.json"
        )
        self._dashboard = self._load()

    def record_snapshot(self, snapshot: ProjectSnapshot) -> None:
        """Record a new project snapshot."""
        self._dashboard.snapshots.append(snapshot)
        self._save()

    def record_attestation(
        self,
        project_name: str,
        attestation: SecurityAttestation,
        confidence_score: int = 0,
    ) -> ProjectSnapshot:
        """Convenience: create and record a snapshot from an attestation."""
        snapshot = ProjectSnapshot.from_attestation(
            project_name, attestation, confidence_score
        )
        self.record_snapshot(snapshot)
        return snapshot

    def get_dashboard(self) -> TeamDashboard:
        return self._dashboard

    def get_summary(self) -> dict:
        return self._dashboard.summary()

    def _load(self) -> TeamDashboard:
        if self._persist_path.exists():
            try:
                data = json.loads(self._persist_path.read_text())
                snapshots = [
                    ProjectSnapshot.from_dict(s) for s in data.get("snapshots", [])
                ]
                return TeamDashboard(team_id=self.team_id, snapshots=snapshots)
            except (json.JSONDecodeError, OSError):
                pass
        return TeamDashboard(team_id=self.team_id)

    def _save(self) -> None:
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "team_id": self.team_id,
            "snapshots": [s.to_dict() for s in self._dashboard.snapshots],
        }
        self._persist_path.write_text(json.dumps(data, indent=2))
