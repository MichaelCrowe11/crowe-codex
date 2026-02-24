"""Threat model engine: evolving threat model per codebase."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from crowe_codex.core.agent import Agent


@dataclass
class Threat:
    """A single identified threat."""

    id: str
    name: str
    category: str  # STRIDE categories
    description: str
    severity: str  # critical, high, medium, low
    mitigation: str = ""
    status: str = "identified"  # identified, mitigated, accepted, transferred

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "severity": self.severity,
            "mitigation": self.mitigation,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Threat:
        return cls(**data)


# STRIDE threat categories
STRIDE = {
    "S": "Spoofing",
    "T": "Tampering",
    "R": "Repudiation",
    "I": "Information Disclosure",
    "D": "Denial of Service",
    "E": "Elevation of Privilege",
}


@dataclass
class ThreatModel:
    """Complete threat model for a codebase."""

    threats: list[Threat] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    trust_boundaries: list[str] = field(default_factory=list)
    data_flows: list[str] = field(default_factory=list)

    @property
    def unmitigated_count(self) -> int:
        return len([t for t in self.threats if t.status == "identified"])

    @property
    def critical_threats(self) -> list[Threat]:
        return [t for t in self.threats if t.severity == "critical"]

    @property
    def summary(self) -> str:
        total = len(self.threats)
        unmitigated = self.unmitigated_count
        critical = len(self.critical_threats)
        return (
            f"Threat Model: {total} threats ({critical} critical, "
            f"{unmitigated} unmitigated)"
        )

    def to_dict(self) -> dict:
        return {
            "threats": [t.to_dict() for t in self.threats],
            "assets": self.assets,
            "trust_boundaries": self.trust_boundaries,
            "data_flows": self.data_flows,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ThreatModel:
        return cls(
            threats=[Threat.from_dict(t) for t in data.get("threats", [])],
            assets=data.get("assets", []),
            trust_boundaries=data.get("trust_boundaries", []),
            data_flows=data.get("data_flows", []),
        )


class ThreatModelEngine:
    """Generates and evolves threat models using cross-vendor AI analysis."""

    def __init__(
        self,
        agents: dict[str, Agent],
        persist_path: Path | None = None,
    ) -> None:
        self._agents = {k: v for k, v in agents.items() if k != "dispatch"}
        self._persist_path = persist_path

    async def analyze(self, code: str, context: str = "") -> ThreatModel:
        """Generate a threat model for the given code."""
        prompt = self._build_analysis_prompt(code, context)

        # Get threat analysis from all available agents
        tasks = {
            name: agent.execute(prompt)
            for name, agent in self._agents.items()
        }
        import asyncio
        results = dict(
            zip(tasks.keys(), await asyncio.gather(*tasks.values()))
        )

        # Merge all agent outputs into a unified threat model
        model = self._merge_results(results)

        if self._persist_path:
            self._save(model)

        return model

    async def evolve(
        self, existing: ThreatModel, new_code: str
    ) -> ThreatModel:
        """Evolve an existing threat model with new code changes."""
        prompt = (
            "An existing threat model needs updating based on new code changes.\n\n"
            f"Existing threats ({len(existing.threats)}):\n"
        )
        for t in existing.threats:
            prompt += f"- [{t.severity.upper()}] {t.name}: {t.description}\n"

        prompt += (
            f"\nNew code changes:\n```\n{new_code}\n```\n\n"
            "Analyze:\n"
            "1. Are any existing threats now mitigated?\n"
            "2. Does the new code introduce new threats?\n"
            "3. Have any threat severities changed?\n\n"
            "Return updated threat list in the same format."
        )

        # Use first available agent for evolution (less critical than initial)
        agent = next(iter(self._agents.values()))
        response = await agent.execute(prompt)

        new_threats = self._parse_threats(response)
        # Merge: keep existing mitigated threats, add new ones
        merged = list(existing.threats)
        existing_names = {t.name for t in merged}
        for t in new_threats:
            if t.name not in existing_names:
                merged.append(t)

        return ThreatModel(
            threats=merged,
            assets=existing.assets,
            trust_boundaries=existing.trust_boundaries,
            data_flows=existing.data_flows,
        )

    def _build_analysis_prompt(self, code: str, context: str) -> str:
        stride_desc = "\n".join(
            f"- {k} ({v})" for k, v in STRIDE.items()
        )
        return (
            "Perform a STRIDE threat model analysis on this code.\n\n"
            f"Code:\n```\n{code}\n```\n\n"
            f"{'Context: ' + context + chr(10) + chr(10) if context else ''}"
            f"STRIDE Categories:\n{stride_desc}\n\n"
            "For each threat found, report:\n"
            "- Threat name\n"
            "- STRIDE category (S/T/R/I/D/E)\n"
            "- Description\n"
            "- Severity (critical/high/medium/low)\n"
            "- Suggested mitigation\n\n"
            "Also identify:\n"
            "- Key assets (data, services, credentials)\n"
            "- Trust boundaries\n"
            "- Data flows\n\n"
            "Format threats as: [CATEGORY] SEVERITY NAME: description | MITIGATION: suggestion"
        )

    def _merge_results(self, results: dict[str, str]) -> ThreatModel:
        """Merge threat analyses from multiple agents."""
        all_threats: list[Threat] = []
        all_assets: set[str] = set()
        all_boundaries: set[str] = set()
        all_flows: set[str] = set()

        threat_counter = 0
        for response in results.values():
            threats = self._parse_threats(response)
            for t in threats:
                threat_counter += 1
                t.id = f"T{threat_counter:03d}"
            all_threats.extend(threats)

        # Deduplicate by name
        seen: dict[str, Threat] = {}
        for t in all_threats:
            if t.name not in seen:
                seen[t.name] = t
            else:
                # Keep the higher severity
                severities = {"critical": 4, "high": 3, "medium": 2, "low": 1}
                if severities.get(t.severity, 0) > severities.get(seen[t.name].severity, 0):
                    seen[t.name] = t

        return ThreatModel(
            threats=list(seen.values()),
            assets=sorted(all_assets),
            trust_boundaries=sorted(all_boundaries),
            data_flows=sorted(all_flows),
        )

    def _parse_threats(self, response: str) -> list[Threat]:
        """Parse agent response into structured threats."""
        threats: list[Threat] = []

        for line in response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Try to match [CATEGORY] SEVERITY NAME: description
            category = ""
            for cat_id in STRIDE:
                if f"[{cat_id}]" in line:
                    category = cat_id
                    break

            if not category:
                continue

            severity = "medium"
            for sev in ("critical", "high", "medium", "low"):
                if sev.upper() in line.upper():
                    severity = sev
                    break

            # Extract mitigation if present
            mitigation = ""
            if "MITIGATION:" in line.upper():
                parts = line.upper().split("MITIGATION:", 1)
                if len(parts) == 2:
                    idx = line.upper().find("MITIGATION:")
                    mitigation = line[idx + 11:].strip()
                    line = line[:idx].strip()

            description = line
            name = f"{STRIDE[category]} threat"

            threats.append(Threat(
                id="",
                name=name,
                category=category,
                description=description,
                severity=severity,
                mitigation=mitigation,
            ))

        return threats

    def _save(self, model: ThreatModel) -> None:
        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            self._persist_path.write_text(json.dumps(model.to_dict(), indent=2))

    def load(self) -> ThreatModel | None:
        if self._persist_path and self._persist_path.exists():
            data = json.loads(self._persist_path.read_text())
            return ThreatModel.from_dict(data)
        return None
