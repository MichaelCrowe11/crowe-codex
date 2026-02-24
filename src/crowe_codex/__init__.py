"""crowe-codex: Cross-vendor adversarial AI code verification engine."""

__version__ = "2.0.0"

from crowe_codex.core.engine import DualEngine
from crowe_codex.core.result import ConfidenceReport, PipelineResult

__all__ = ["DualEngine", "ConfidenceReport", "PipelineResult"]
