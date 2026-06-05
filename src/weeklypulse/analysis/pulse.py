"""Pulse generator (Phase 3, Activity 3.6).

Composes the weekly pulse from themes, quotes, and actions.
Enforces the ≤250-word limit per ADR-018 (body only; headings excluded).
LLM-assisted action ideas and pulse polish via Groq (ADR-006).
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from weeklypulse.analysis.models import ActionIdea, Pulse, Quote, Theme
from weeklypulse.config import REPO_ROOT, resolve_path

logger = logging.getLogger(__name__)


# ── Pulse markdown template ──────────────────────────────────────────────

_HEADER_TEMPLATE = """\
WeeklyPulse — {app_name}
Week: {week_label} ({date_range})
Generated: {generated_date}
"""

_THEMES_SECTION = """\
## Top themes this week
{theme_lines}
"""

_QUOTES_SECTION = """\
## What users said
{quote_lines}
"""

_ACTIONS_SECTION = """\
## Suggested actions
{action_lines}
"""


def _theme_lines(themes: list[Theme]) -> str:
    """Format top 3 themes as numbered bullets."""
    top = sorted(
        [t for t in themes if t.top_rank >= 1], key=lambda t: t.top_rank
    )
    lines: list[str] = []
    for t in top:
        pct = int(t.low_rating_share * 100)
        lines.append(
            f"{t.top_rank}. {t.label} — {t.description} "
            f"({t.review_count} reviews, {pct}% low-rated)"
        )
    return "\n".join(lines)


def _quote_lines(quotes: list[Quote]) -> str:
    """Format quotes as bullet list with rating/platform context."""
    lines: list[str] = []
    for q in quotes:
        stars = "\u2605" * q.source_rating
        lines.append(
            f'- "{q.text}" \u2014 {stars}, {q.source_platform}'
        )
    return "\n".join(lines)


def _action_lines(actions: list[ActionIdea]) -> str:
    """Format action ideas as numbered list."""
    lines: list[str] = []
    for i, a in enumerate(actions, 1):
        kind_tag = f" [{a.kind}]" if a.kind else ""
        lines.append(f"{i}. {a.text}{kind_tag}")
    return "\n".join(lines)


def compose_pulse_md(pulse: Pulse) -> str:
    """Compose full pulse markdown from a Pulse object."""
    header = _HEADER_TEMPLATE.format(
        app_name=pulse.app_name,
        week_label=pulse.week_label,
        date_range=pulse.date_range,
        generated_date=pulse.generated_date,
    )

    themes_section = _THEMES_SECTION.format(theme_lines=_theme_lines(pulse.themes))
    quotes_section = _QUOTES_SECTION.format(quote_lines=_quote_lines(pulse.quotes))
    actions_section = _ACTIONS_SECTION.format(action_lines=_action_lines(pulse.actions))

    return header + themes_section + quotes_section + actions_section


def body_text(md: str) -> str:
    """Extract body text (exclude header and section headings) for word count.

    ADR-018: word limit applies to body only; headings and header lines
    do not count.
    """
    lines: list[str] = []
    for line in md.splitlines():
        stripped = line.strip()
        # Skip header lines (before first ##) and section headings
        if stripped.startswith("WeeklyPulse —"):
            continue
        if stripped.startswith("Week:"):
            continue
        if stripped.startswith("Generated:"):
            continue
        if stripped.startswith("## "):
            continue
        if not stripped:
            continue
        lines.append(stripped)
    return " ".join(lines)


def count_body_words(md: str) -> int:
    """Count words in pulse body (ADR-018: headings excluded)."""
    body = body_text(md)
    return len(body.split())


def generate_default_actions(themes: list[Theme]) -> list[ActionIdea]:
    """Generate template action ideas from top themes.

    These are basic, data-driven suggestions. The AI agent should
    refine them for specificity and Groww context.
    """
    top = sorted(
        [t for t in themes if t.top_rank >= 1], key=lambda t: t.top_rank
    )

    actions: list[ActionIdea] = []
    for t in top:
        if t.low_rating_share > 0.5:
            kind = "investigative"
        elif t.review_count > 50:
            kind = "quick-win"
        else:
            kind = "cross-functional"

        actions.append(
            ActionIdea(
                text=f"Review {t.label} feedback and prioritize top complaints",
                theme_label=t.label,
                kind=kind,
            )
        )

    # Fill to 3 if needed
    while len(actions) < 3:
        actions.append(
            ActionIdea(
                text="Review user feedback for emerging issues",
                theme_label="general",
                kind="investigative",
            )
        )

    return actions[:3]


def trim_to_word_limit(md: str, limit: int = 250) -> str:
    """Trim pulse body to *limit* words by truncating last action if needed.

    ADR-018: body only. If over limit, trims the last action idea text.
    """
    word_count = count_body_words(md)
    if word_count <= limit:
        return md

    # Strategy: shorten action text iteratively
    lines = md.splitlines()
    # Find last action line and truncate
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line and line[0].isdigit() and "." in line:
            # This is an action line — trim it
            words = line.split()
            excess = word_count - limit
            if excess > 0 and len(words) > excess + 3:
                lines[i] = " ".join(words[: -excess]) + "..."
                break

    return "\n".join(lines)


def write_pulse_files(
    pulse: Pulse, md: str, cfg: dict[str, Any]
) -> dict[str, str]:
    """Write pulse.md and pulse.json to configured output paths.

    Returns dict with output file paths.
    """
    md_path = resolve_path(cfg, "analysis.pulse_markdown_output")
    json_path = resolve_path(cfg, "analysis.pulse_json_output")

    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    md_path.write_text(md, encoding="utf-8")

    pulse_data = pulse.to_dict()
    json_path.write_text(
        json.dumps(pulse_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return {
        "pulse_md": str(md_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "pulse_json": str(json_path.relative_to(REPO_ROOT)).replace("\\", "/"),
    }


def write_themes_json(themes: list[Theme], cfg: dict[str, Any]) -> str:
    """Write themes.json to configured output path.

    Returns relative path.
    """
    themes_path = resolve_path(cfg, "analysis.themes_output")
    themes_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "theme_count": len(themes),
        "themes": [t.to_dict() for t in themes],
    }

    themes_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return str(themes_path.relative_to(REPO_ROOT)).replace("\\", "/")


def generate_actions_with_llm(
    themes: list[Theme],
    quotes: list[Quote],
    model: str = "llama-3.3-70b-versatile",
) -> list[ActionIdea]:
    """Use Groq LLM to generate specific, actionable ideas (ADR-006).

    Falls back to deterministic generate_default_actions on failure.
    """
    from weeklypulse.analysis.llm import generate_actions_with_llm as llm_gen

    top = sorted(
        [t for t in themes if t.top_rank >= 1], key=lambda t: t.top_rank
    )

    # Build inputs for LLM
    theme_dicts = [
        {
            "label": t.label,
            "description": t.description,
            "review_count": t.review_count,
        }
        for t in top
    ]
    quote_dicts = [
        {"text": q.text, "theme_label": q.theme_label}
        for q in quotes
    ]

    llm_actions = llm_gen(theme_dicts, quote_dicts, model=model)

    if not llm_actions:
        logger.warning("LLM action generation failed; using deterministic defaults")
        return generate_default_actions(themes)

    actions: list[ActionIdea] = []
    for a in llm_actions[:3]:
        actions.append(
            ActionIdea(
                text=a.get("text", "Review user feedback"),
                theme_label=a.get("theme_label", "general"),
                kind=a.get("kind", "investigative"),
            )
        )

    # Pad if fewer than 3
    while len(actions) < 3:
        defaults = generate_default_actions(themes)
        actions.append(defaults[len(actions)])
        break

    return actions[:3]


def polish_pulse_with_llm(
    draft_md: str,
    model: str = "llama-3.3-70b-versatile",
    max_tokens: int = 1024,
) -> str | None:
    """Use Groq LLM to polish the pulse for readability (ADR-006).

    Returns polished markdown, or None on failure (caller keeps draft).
    """
    from weeklypulse.analysis.llm import polish_pulse_with_llm as llm_polish

    result = llm_polish(draft_md, model=model, max_tokens=max_tokens)

    if result is None:
        logger.warning("LLM pulse polish failed; keeping deterministic draft")
    return result
