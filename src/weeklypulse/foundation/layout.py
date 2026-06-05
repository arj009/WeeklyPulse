"""Project and data directory layout (Phase 1)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Data paths used across phases
DATA_DIRS = (
    "data/raw",
    "data/processed",
    "data/output",
    "data/fixtures",
    "data/runs",
    "data/runs/example",
)

# Phase implementation roots (code stubs)
PHASE_SRC_DIRS = (
    "src/weeklypulse/foundation",
    "src/weeklypulse/ingestion",
    "src/weeklypulse/analysis",
    "src/weeklypulse/delivery",
    "src/weeklypulse/e2e",
)


def ensure_data_layout() -> None:
    """Create data directories and .gitkeep where needed."""
    for rel in DATA_DIRS:
        path = REPO_ROOT / rel
        path.mkdir(parents=True, exist_ok=True)
        gitkeep = path / ".gitkeep"
        if not any(path.iterdir()) and not gitkeep.exists():
            gitkeep.touch(exist_ok=True)
