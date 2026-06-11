"""Phase 3 — Analysis and pulse generation.

Orchestrates: cluster → rank → (LLM label) → quotes → (LLM actions) →
compose → (LLM polish) → PII gate → write.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

from weeklypulse.analysis.models import Pulse
from weeklypulse.analysis.pii_guard import pii_gate
from weeklypulse.analysis.pulse import (
    compose_pulse_md,
    count_body_words,
    generate_actions_with_llm,
    generate_default_actions,
    polish_pulse_with_llm,
    trim_to_word_limit,
    write_pulse_files,
    write_themes_json,
)
from weeklypulse.analysis.quotes import select_quotes
from weeklypulse.analysis.ranking import rank_themes, ranking_rationale
from weeklypulse.analysis.themes import cluster_reviews, refine_themes_with_llm
from weeklypulse.config import REPO_ROOT, resolve_path
from weeklypulse.ingestion.models import Review

__all__ = ["run_analysis"]

logger = logging.getLogger(__name__)


def _load_reviews(reviews_path: Path) -> list[Review]:
    """Load reviews from JSONL file produced by Phase 2 ingestion."""
    reviews: list[Review] = []
    with reviews_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            reviews.append(
                Review(
                    id=data["id"],
                    platform=data["platform"],
                    rating=data["rating"],
                    title=data.get("title", ""),
                    text=data.get("text", ""),
                    review_date=data["review_date"],
                    source_file=data.get("source_file", ""),
                )
            )
    return reviews


def _week_label(as_of: date) -> str:
    """ISO week label e.g. '2026-W22'."""
    return as_of.strftime("%G-W%V")


def _date_range(reviews: list[Review]) -> str:
    """Date range string from review dates."""
    if not reviews:
        return "N/A"
    dates = sorted(r.review_date for r in reviews)
    return f"{dates[0]} to {dates[-1]}"


def run_analysis(
    cfg: dict[str, Any],
    *,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Run the full Phase 3 analysis pipeline.

    Steps:
    1. Load reviews.jsonl
    2. Cluster into themes (≤5)
    3. Rank themes (ADR-007)
    4. Select 3 quotes (ADR-014, PII redacted)
    5. Generate 3 action ideas
    6. Compose pulse (≤250 words, ADR-018)
    7. PII gate (fail-closed, ADR-005)
    8. Write output files

        Returns analysis summary dict.
    """
    ana = cfg["analysis"]
    max_themes = int(ana.get("max_themes", 5))
    top_n = int(ana.get("top_themes_in_pulse", 3))
    quotes_count = int(ana.get("quotes_count", 3))
    word_limit = int(ana.get("pulse_word_limit", 250))
    llm_enabled = bool(ana.get("llm_enabled", False))
    llm_model = ana.get("llm_model", "llama-3.3-70b-versatile")
    llm_max_tokens = int(ana.get("llm_max_tokens", 1024))

    # --- Step 1: Load reviews ---
    reviews_path = resolve_path(cfg, "ingestion.processed_output")
    if not reviews_path.is_file():
        raise FileNotFoundError(f"Reviews file not found: {reviews_path}")

    reviews = _load_reviews(reviews_path)

    if not reviews:
        return {
            "status": "error",
            "message": "No reviews to analyze",
            "review_count": 0,
        }

    # --- Step 2: Cluster into themes (deterministic) ---
    themes = cluster_reviews(reviews, max_themes=max_themes)

    # --- Step 3: Rank themes (ADR-007) ---
    themes = rank_themes(themes, top_n=top_n)
    rationale = ranking_rationale(themes)

    # --- Step 3b: LLM theme labeling (ADR-006) ---
    if llm_enabled:
        from weeklypulse.analysis.llm import is_llm_available
        if is_llm_available():
            logger.info("LLM enabled: refining theme labels with Groq")
            themes = refine_themes_with_llm(themes, reviews, model=llm_model)
        else:
            logger.warning("LLM enabled in config but GROQ_API_KEY not set; skipping")

    # --- Step 4: Select quotes ---
    quotes = select_quotes(themes, reviews, count=quotes_count)

    # --- Step 5: Generate action ideas (LLM or deterministic) ---
    if llm_enabled:
        from weeklypulse.analysis.llm import is_llm_available
        if is_llm_available():
            logger.info("LLM enabled: generating action ideas with Groq")
            actions = generate_actions_with_llm(themes, quotes, model=llm_model)
        else:
            actions = generate_default_actions(themes)
    else:
        actions = generate_default_actions(themes)
    
    # --- Step 5b: Sentiment analysis (LLM-powered) ---
    sentiment = {"positive": 0, "negative": 0, "neutral": 0}
    if llm_enabled:
        from weeklypulse.analysis.llm import is_llm_available, analyze_sentiment_with_llm
        if is_llm_available():
            logger.info("LLM enabled: analyzing sentiment with Groq")
            sentiment = analyze_sentiment_with_llm(reviews, model=llm_model)
            logger.info(f"Sentiment: {sentiment}")

    # --- Step 6: Compose pulse ---
    as_of_d = (
        datetime.strptime(as_of, "%Y-%m-%d").date() if as_of else date.today()
    )
    pulse = Pulse(
        app_name=cfg["app"]["name"],
        week_label=_week_label(as_of_d),
        date_range=_date_range(reviews),
        generated_date=as_of_d.isoformat(),
        themes=themes,
        quotes=quotes,
        actions=actions,
        sentiment=sentiment,
    )

    md = compose_pulse_md(pulse)

    # --- Step 6b: LLM pulse polish (ADR-006) ---
    if llm_enabled:
        from weeklypulse.analysis.llm import is_llm_available
        if is_llm_available():
            logger.info("LLM enabled: polishing pulse with Groq")
            polished = polish_pulse_with_llm(
                md, model=llm_model, max_tokens=llm_max_tokens
            )
            if polished is not None:
                md = polished
                pulse.body_word_count = count_body_words(md)

    # Enforce word limit (ADR-018)
    body_words = count_body_words(md)
    if body_words > word_limit:
        md = trim_to_word_limit(md, word_limit)
        body_words = count_body_words(md)

    pulse.body_word_count = body_words

    # --- Step 7: PII gate ---
    gate_result = pii_gate(md)
    pulse.pii_gate = "pass" if gate_result["passed"] else "fail"

    # --- Step 8: Write output files ---
    themes_path = write_themes_json(themes, cfg)
    pulse_files = write_pulse_files(pulse, md, cfg)

    # --- Build summary ---
    summary: dict[str, Any] = {
        "status": "ok" if gate_result["passed"] else "pii_failed",
        "review_count": len(reviews),
        "theme_count": len(themes),
        "themes": [
            {
                "label": t.label,
                "review_count": t.review_count,
                "top_rank": t.top_rank,
            }
            for t in themes
        ],
        "top_3": [t.label for t in themes if t.top_rank >= 1],
        "top_3_rationale": rationale,
        "quotes_selected": len(quotes),
        "quote_source_ids": [q.source_review_id for q in quotes],
        "body_word_count": body_words,
        "word_limit": word_limit,
        "within_word_limit": body_words <= word_limit,
        "pii_gate": pulse.pii_gate,
        "pii_violations": gate_result["violation_count"],
        "llm_enabled": llm_enabled,
        "llm_model": llm_model if llm_enabled else None,
        "themes_json": themes_path,
        "pulse_md": md,  # Full pulse markdown for delivery
        "week_label": pulse.week_label,  # Week label for delivery
        "sentiment": sentiment,  # Sentiment analysis for delivery
        **pulse_files,
    }

    if not gate_result["passed"]:
        summary["message"] = (
            f"PII gate FAILED with {gate_result['violation_count']} violation(s). "
            "Fix pulse before Phase 4 delivery."
        )

    return summary

