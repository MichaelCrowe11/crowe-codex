"""Pipeline stage sequencing and skip logic."""

from __future__ import annotations

from crowe_codex.core.result import Stage

STAGE_PRESETS: dict[str, list[Stage]] = {
    "trivial": [Stage.ARCHITECT, Stage.DISPATCH],
    "standard": [Stage.ARCHITECT, Stage.BUILDER, Stage.DISPATCH],
    "security": [Stage.ARCHITECT, Stage.BUILDER, Stage.SPECIALIST, Stage.DISPATCH],
    "performance": [Stage.ARCHITECT, Stage.BUILDER, Stage.ACCELERATOR, Stage.DISPATCH],
    "full": [Stage.ARCHITECT, Stage.BUILDER, Stage.SPECIALIST, Stage.ACCELERATOR, Stage.DISPATCH],
    "audit": [Stage.ARCHITECT, Stage.SPECIALIST, Stage.DISPATCH],
}


def resolve_stages(
    requested: list[Stage] | None,
    available: list[int],
    preset: str | None = None,
) -> list[Stage]:
    """Determine which stages to run based on request and availability."""
    if preset and preset in STAGE_PRESETS:
        stages = STAGE_PRESETS[preset]
    elif requested:
        stages = requested
    else:
        stages = STAGE_PRESETS["standard"]

    return [s for s in stages if s.value in available]
