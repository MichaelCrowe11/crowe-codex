"""claude-codex: Cross-vendor adversarial AI code verification engine."""

__version__ = "0.1.0"

from claude_codex.core.engine import DualEngine
from claude_codex.core.result import ConfidenceReport, PipelineResult

__all__ = ["DualEngine", "ConfidenceReport", "PipelineResult"]
