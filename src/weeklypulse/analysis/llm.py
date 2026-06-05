"""Groq LLM integration for agent-assisted synthesis (ADR-006).

Provides three LLM-powered capabilities:
1. Theme labeling — name clusters from actual review content
2. Action idea generation — specific, actionable next steps
3. Pulse polish — refine tone, brevity, and Groww relevance

All calls have deterministic fallbacks when LLM is unavailable.
"""

from __future__ import annotations

import json
import os
from typing import Any


def _get_client() -> Any:
    """Lazily create a Groq client from GROQ_API_KEY env var."""
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment")
    return Groq(api_key=api_key)


def _chat(
    system_prompt: str,
    user_prompt: str,
    model: str = "llama-3.3-70b-versatile",
    max_tokens: int = 1024,
    temperature: float = 0.3,
) -> str:
    """Send a chat completion request to Groq and return the content."""
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


# ── 1. Theme labeling ────────────────────────────────────────────────────


_SYSTEM_LABEL_THEMES = """\
You are a product analyst for Groww (Indian fintech / investing app).
You receive clusters of user reviews and must assign each cluster a
concise, recognizable theme label (2–4 words) and a one-line description.

Rules:
- Labels must be specific to fintech / investing (not generic like "Other")
- Descriptions should explain what users are experiencing in that cluster
- Return ONLY valid JSON: {"themes": [{"slug": "...", "label": "...", "description": "..."}, ...]}
- No markdown formatting, no code fences, no extra commentary
"""


def label_themes_with_llm(
    theme_data: list[dict[str, Any]],
    model: str = "llama-3.3-70b-versatile",
) -> dict[str, dict[str, str]]:
    """Ask Groq to name themes based on sample review text.

    Args:
        theme_data: list of dicts with keys: slug, review_count, sample_reviews (list[str])

    Returns:
        dict mapping slug → {"label": ..., "description": ...}
    """
    user_parts: list[str] = []
    for td in theme_data:
        samples = td.get("sample_reviews", [])[:5]  # max 5 samples per theme
        user_parts.append(
            f"Cluster '{td['slug']}' ({td['review_count']} reviews):\n"
            + "\n".join(f'  - "{s}"' for s in samples)
        )

    user_prompt = "Name and describe each cluster:\n\n" + "\n\n".join(user_parts)

    try:
        raw = _chat(_SYSTEM_LABEL_THEMES, user_prompt, model=model)
        # Strip possible markdown fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        parsed = json.loads(raw)
        result: dict[str, dict[str, str]] = {}
        for item in parsed.get("themes", []):
            slug = item.get("slug", "")
            if slug:
                result[slug] = {
                    "label": item.get("label", slug),
                    "description": item.get("description", ""),
                }
        return result
    except Exception:
        return {}


# ── 2. Action idea generation ────────────────────────────────────────────


_SYSTEM_ACTIONS = """\
You are a product manager for Groww (Indian fintech / investing app).
Given the top themes and representative user quotes from this week's
reviews, generate exactly 3 concrete action ideas.

Rules:
- Each action must be specific enough for a PM or support lead to act on
- NOT vague like "Fix app" or "Improve experience"
- Each action should reference the specific issue users are facing
- Assign a kind: "quick-win" (can ship this week), "investigative" (needs
  research), or "cross-functional" (needs multiple teams)
- Return ONLY valid JSON: {"actions": [{"text": "...", "theme_label": "...", "kind": "..."}, ...]}
- No markdown formatting, no code fences, no extra commentary
"""


def generate_actions_with_llm(
    themes: list[dict[str, Any]],
    quotes: list[dict[str, Any]],
    model: str = "llama-3.3-70b-versatile",
) -> list[dict[str, str]]:
    """Ask Groq to generate 3 specific action ideas.

    Args:
        themes: top themes with label, description, review_count
        quotes: selected quotes with text and theme_label

    Returns:
        list of action dicts with text, theme_label, kind
    """
    theme_summary = "\n".join(
        f"- {t['label']}: {t['description']} ({t['review_count']} reviews)"
        for t in themes
    )
    quote_summary = "\n".join(
        f'- "{q["text"]}" (theme: {q["theme_label"]})' for q in quotes
    )

    user_prompt = (
        f"Top themes this week:\n{theme_summary}\n\n"
        f"User quotes:\n{quote_summary}\n\n"
        "Generate 3 action ideas."
    )

    try:
        raw = _chat(_SYSTEM_ACTIONS, user_prompt, model=model)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        parsed = json.loads(raw)
        return parsed.get("actions", [])
    except Exception:
        return []


# ── 3. Pulse polish ──────────────────────────────────────────────────────


_SYSTEM_POLISH = """\
You are a product communication specialist for Groww (Indian fintech / investing app).
You receive a draft weekly pulse and must polish it for executive readability.

Rules:
- Keep the same structure: themes, quotes, actions
- Do NOT change quotes — they must remain verbatim from users
- Improve theme descriptions to be concise and actionable
- Tighten action wording to be specific and direct
- Total body text must stay under 250 words (headings don't count)
- Return ONLY the polished markdown text — no JSON, no code fences, no commentary
- Do not add any personal information, usernames, emails, or IDs
- Start with the header line "WeeklyPulse — Groww"
"""


def polish_pulse_with_llm(
    draft_md: str,
    model: str = "llama-3.3-70b-versatile",
    max_tokens: int = 1024,
) -> str | None:
    """Ask Groq to polish the draft pulse for readability and brevity.

    Returns polished markdown, or None on failure.
    """
    user_prompt = f"Polish this weekly pulse:\n\n{draft_md}"

    try:
        result = _chat(_SYSTEM_POLISH, user_prompt, model=model, max_tokens=max_tokens)
        # Strip code fences if present
        if result.startswith("```"):
            result = result.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        return result if "WeeklyPulse" in result else None
    except Exception:
        return None


# ── Convenience: check if LLM is available ────────────────────────────────


def is_llm_available() -> bool:
    """Return True if GROQ_API_KEY is set and the groq package is importable."""
    if not os.environ.get("GROQ_API_KEY", ""):
        return False
    try:
        import groq  # noqa: F401
        return True
    except ImportError:
        return False
