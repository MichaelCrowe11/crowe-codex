"""Pipeline result types and confidence scoring."""

from __future__ import annotations

from enum import IntEnum

from pydantic import BaseModel, computed_field


class Stage(IntEnum):
    """Pipeline stages."""

    ARCHITECT = 1
    BUILDER = 2
    SPECIALIST = 3
    ACCELERATOR = 4
    DISPATCH = 5


class AgentOutput(BaseModel):
    """Output from a single agent in the pipeline."""

    stage: Stage
    agent_name: str
    content: str
    metadata: dict[str, object] = {}


class SecurityAttestation(BaseModel):
    """Security verification report."""

    owasp_clean: bool = False
    dependencies_verified: bool = False
    supply_chain_risks: int = 0
    vulnerabilities_found: int = 0
    attacks_survived: int = 0
    compliance_checks: dict[str, bool] = {}


class ConfidenceReport(BaseModel):
    """Confidence scoring across the pipeline."""

    architecture_preserved: bool
    tests_passing: bool
    vulnerabilities_found: int
    dependencies_verified: bool
    owasp_clean: bool
    models_consulted: int
    cross_vendor_agreement: float

    @computed_field
    @property
    def score(self) -> int:
        """Calculate confidence score 0-100."""
        s = 0
        if self.architecture_preserved:
            s += 20
        if self.tests_passing:
            s += 20
        if self.vulnerabilities_found == 0:
            s += 15
        if self.dependencies_verified:
            s += 15
        if self.owasp_clean:
            s += 15
        s += int(self.cross_vendor_agreement * 15)
        return min(s, 100)


class PipelineResult(BaseModel):
    """Final output from the claude-codex pipeline."""

    code: str
    stage_outputs: list[AgentOutput] = []
    confidence: ConfidenceReport
    security: SecurityAttestation
    summary: str = ""
