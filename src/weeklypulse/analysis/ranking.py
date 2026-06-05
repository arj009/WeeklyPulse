"""Theme ranking per ADR-007 (Phase 3, Activity 3.3).

Hybrid ranking:
1. Primary: review count (descending)
2. Tie-break: higher share of 1-2 star reviews (severity signal)
3. Second tie-break: alphabetical theme label (deterministic)
"""

from __future__ import annotations

from weeklypulse.analysis.models import Theme


def rank_themes(themes: list[Theme], top_n: int = 3) -> list[Theme]:
    """Sort themes by ADR-007 rule and mark top *top_n*.

    Returns a **new** sorted list with ``top_rank`` set on the
    top *top_n* themes (1 = highest, *top_n* = lowest of the top).
    Remaining themes get ``top_rank = 0``.
    """
    sorted_themes = sorted(
        themes,
        key=lambda t: (
            -t.review_count,       # primary: more reviews first
            -t.low_rating_share,   # tie-break: more severity first
            t.label.lower(),       # second tie-break: alphabetical
        ),
    )

    for i, theme in enumerate(sorted_themes):
        theme.top_rank = i + 1 if i < top_n else 0

    return sorted_themes


def top_themes(themes: list[Theme]) -> list[Theme]:
    """Return only themes with ``top_rank >= 1``, sorted by rank."""
    return sorted(
        [t for t in themes if t.top_rank >= 1],
        key=lambda t: t.top_rank,
    )


def ranking_rationale(themes: list[Theme]) -> str:
    """One-sentence rationale for why the top 3 were chosen (manifest field)."""
    top = top_themes(themes)
    if not top:
        return "No themes ranked."

    parts = [
        f"{t.label} ({t.review_count} reviews, {t.low_rating_share:.0%} low-rated)"
        for t in top
    ]
    return "Top themes by review volume and severity: " + "; ".join(parts) + "."
