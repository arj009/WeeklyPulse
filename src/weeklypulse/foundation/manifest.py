"""Run manifest template helpers (Phase 1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = REPO_ROOT / "templates" / "manifest.template.json"


def manifest_template_path() -> Path:
    return TEMPLATE_PATH


def load_manifest_template() -> dict[str, Any]:
    if not TEMPLATE_PATH.is_file():
        raise FileNotFoundError(f"Manifest template missing: {TEMPLATE_PATH}")
    with TEMPLATE_PATH.open(encoding="utf-8") as f:
        return json.load(f)
