"""Quote selection with PII redaction (Phase 3, Activity 3.4).

Selects representative quotes from top themes, redacts PII,
and ensures each quote is verbatim from source reviews (ADR-014).
"""

from __future__ import annotations

from typing import Any

from weeklypulse.analysis.models import Quote, Theme
from weeklypulse.analysis.pii_guard import redact_pii
from weeklypulse.ingestion.models import Review


def select_quotes(
    themes: list[Theme],
    reviews: list[Review],
    count: int = 3,
    min_quote_words: int = 6,
    max_quote_words: int = 50,
) -> list[Quote]:
    """Select *count* quotes from top-ranked themes.

    Strategy:
    1. Pick one quote per top theme (up to *count* themes).
    2. Prefer longer, substantive reviews over short ones.
    3. Prefer reviews from different platforms for variety.
    4. Redact PII before returning (ADR-014: verbatim after redaction).
    5. Skip quotes that become too short after redaction.
    """
    top = [t for t in themes if t.top_rank >= 1]
    top = sorted(top, key=lambda t: t.top_rank)[:count]

    if not top:
        # Fallback: pick from all themes by review count
        top = sorted(themes, key=lambda t: t.review_count, reverse=True)[:count]

    # Build lookup: review_id → Review
    review_map: dict[str, Review] = {r.id: r for r in reviews}

    quotes: list[Quote] = []
    used_platforms: list[str] = []

    for theme in top:
        quote = _pick_best_quote(
            theme=theme,
            review_map=review_map,
            used_platforms=used_platforms,
            min_words=min_quote_words,
            max_words=max_quote_words,
        )
        if quote is not None:
            quotes.append(quote)
            used_platforms.append(quote.source_platform)

    # If fewer quotes than requested, fill from remaining themes
    if len(quotes) < count:
        used_ids = {q.source_review_id for q in quotes}
        remaining_themes = [t for t in themes if t not in top]
        for theme in remaining_themes:
            if len(quotes) >= count:
                break
            quote = _pick_best_quote(
                theme=theme,
                review_map=review_map,
                used_platforms=used_platforms,
                min_words=min_quote_words,
                max_words=max_quote_words,
                exclude_ids=used_ids,
            )
            if quote is not None:
                quotes.append(quote)
                used_platforms.append(quote.source_platform)

    return quotes[:count]


def _pick_best_quote(
    *,
    theme: Theme,
    review_map: dict[str, Review],
    used_platforms: list[str],
    min_words: int,
    max_words: int,
    exclude_ids: set[str] | None = None,
) -> Quote | None:
    """Pick the best quote from a single theme's reviews.

    Scoring heuristic:
    - Prefer reviews not from already-used platforms (diversity)
    - Prefer substantive text (longer, more words)
    - Prefer lower ratings (more actionable feedback)
    """
    exclude = exclude_ids or set()
    candidates: list[dict[str, Any]] = []

    for rid in theme.review_ids:
        if rid in exclude:
            continue
        rev = review_map.get(rid)
        if rev is None:
            continue

        text = rev.text.strip()
        if not text:
            continue

        word_count = len(text.split())
        if word_count < min_words or word_count > max_words:
            continue

        # Score: platform diversity + length + lower rating
        platform_bonus = 1 if rev.platform not in used_platforms else 0
        score = platform_bonus * 100 + word_count + (6 - rev.rating) * 10

        candidates.append({"review": rev, "score": score, "word_count": word_count})

    if not candidates:
        return None

    # Pick highest-scored candidate
    best = max(candidates, key=lambda c: c["score"])
    rev = best["review"]

    # Redact PII (ADR-014: verbatim after redaction)
    redacted_text, redaction_count = redact_pii(rev.text.strip())

    # Skip if redaction made quote too short
    if len(redacted_text.split()) < min_words:
        # Try the next best candidate
        for cand in sorted(candidates, key=lambda c: c["score"], reverse=True):
            if cand["review"].id == rev.id:
                continue
            r = cand["review"]
            rt, _ = redact_pii(r.text.strip())
            if len(rt.split()) >= min_words:
                return Quote(
                    text=rt,
                    source_review_id=r.id,
                    source_rating=r.rating,
                    source_platform=r.platform,
                    theme_label=theme.label,
                )
        return None

    return Quote(
        text=redacted_text,
        source_review_id=rev.id,
        source_rating=rev.rating,
        source_platform=rev.platform,
        theme_label=theme.label,
    )
