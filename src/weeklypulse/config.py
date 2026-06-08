"""Load and validate WeeklyPulse configuration."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

REQUIRED_TOP_LEVEL = ("app", "ingestion", "analysis", "delivery", "runs", "manifest")

# Try multiple strategies to find repo root
def _find_repo_root() -> Path:
    """Find the repository root by looking for config/default.yaml."""
    current = Path(__file__).resolve().parent
    
    # Strategy 1: Search up to 5 levels for config/default.yaml
    for _ in range(5):
        config_path = current / "config" / "default.yaml"
        if config_path.is_file():
            return current
        current = current.parent
    
    # Strategy 2: Check /opt/render/project/src (Render deployment)
    render_path = Path("/opt/render/project/src")
    if (render_path / "config" / "default.yaml").is_file():
        return render_path
    
    # Fallback
    return Path(__file__).resolve().parents[2]

REPO_ROOT = _find_repo_root()
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "default.yaml"


class ConfigError(Exception):
    """Invalid or missing configuration."""


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):

        def repl(match: re.Match[str]) -> str:
            inner = match.group(1)
            if ":" in inner:
                key, default = inner.split(":", 1)
                return os.environ.get(key, default)
            return os.environ.get(inner, "")

        return re.sub(r"\$\{([^}]+)\}", repl, value)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or Path(
        os.environ.get("WEEKLYPULSE_CONFIG", str(DEFAULT_CONFIG_PATH))
    )
    if not config_path.is_file():
        raise ConfigError(f"Config file not found: {config_path}")

    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ConfigError("Config root must be a mapping")

    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            raise ConfigError(f"Missing required config section: {key}")

    data = _expand_env(data)
    _validate(data)
    return data


def _validate(cfg: dict[str, Any]) -> None:
    app = cfg["app"]
    if not app.get("name"):
        raise ConfigError("app.name is required")

    ing = cfg["ingestion"]
    weeks = ing.get("review_window_weeks")
    wmin = ing.get("review_window_min_weeks", 8)
    wmax = ing.get("review_window_max_weeks", 12)
    if weeks is None or not (wmin <= weeks <= wmax):
        raise ConfigError(
            f"ingestion.review_window_weeks must be between {wmin} and {wmax}"
        )

    ana = cfg["analysis"]
    if ana.get("max_themes", 0) > 5:
        raise ConfigError("analysis.max_themes must be <= 5")
    if ana.get("top_themes_in_pulse", 0) > 3:
        raise ConfigError("analysis.top_themes_in_pulse must be <= 3")
    if ana.get("pulse_word_limit", 0) > 250:
        raise ConfigError("analysis.pulse_word_limit must be <= 250")

    delivery = cfg["delivery"]
    if not delivery.get("subject_pattern") or not delivery.get("doc_title_pattern"):
        raise ConfigError("delivery subject_pattern and doc_title_pattern are required")


def resolve_path(cfg: dict[str, Any], key_path: str) -> Path:
    """Resolve a config path relative to repo root."""
    parts = key_path.split(".")
    node: Any = cfg
    for p in parts:
        node = node[p]
    return REPO_ROOT / str(node)
