"""Ingestion pipeline orchestration."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from weeklypulse.config import REPO_ROOT, resolve_path
from weeklypulse.ingestion.filters import apply_content_filters
from weeklypulse.ingestion.models import Review
from weeklypulse.ingestion.parsers.registry import parse_export_file


def _as_of_date(cfg: dict[str, Any], as_of: str | None) -> date:
    if as_of:
        return datetime.strptime(as_of, "%Y-%m-%d").date()
    return date.today()


def _in_window(review_date: date, as_of: date, window_weeks: int) -> bool:
    start = as_of - timedelta(weeks=window_weeks)
    return start <= review_date <= as_of


def dedupe_reviews(reviews: list[Review]) -> tuple[list[Review], int]:
    """ADR-016: keep latest review_date per id."""
    by_id: dict[str, Review] = {}
    for r in reviews:
        existing = by_id.get(r.id)
        if existing is None or r.review_date > existing.review_date:
            by_id[r.id] = r
    removed = len(reviews) - len(by_id)
    return list(by_id.values()), removed


def run_ingestion(
    cfg: dict[str, Any],
    input_dir: Path | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    ing = cfg["ingestion"]
    raw_dir = input_dir or (REPO_ROOT / ing["raw_input_dir"])
    output_path = resolve_path(cfg, "ingestion.processed_output")
    window_weeks = int(ing["review_window_weeks"])
    as_of_d = _as_of_date(cfg, as_of)

    min_words = int(ing.get("min_words", 6))
    english_only = bool(ing.get("english_only", True))
    reject_emojis = bool(ing.get("reject_emojis", True))
    lang_min = float(ing.get("language_confidence_min", 0.7))

    files = sorted(
        p
        for p in raw_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {".csv", ".tsv", ".txt"}
    )
    if not files:
        raise FileNotFoundError(f"No CSV exports in {raw_dir}")

    all_parsed: list[Review] = []
    parse_errors: list[dict[str, Any]] = []
    files_loaded: list[str] = []

    for path in files:
        reviews, errors, _platform = parse_export_file(path)
        all_parsed.extend(reviews)
        parse_errors.extend(errors)
        files_loaded.append(path.name)

    filter_stats: Counter[str] = Counter()
    window_excluded = 0
    kept: list[Review] = []

    for r in all_parsed:
        rd = datetime.strptime(r.review_date, "%Y-%m-%d").date()
        if not _in_window(rd, as_of_d, window_weeks):
            window_excluded += 1
            continue

        combined = r.combined_text()
        ok, reason = apply_content_filters(
            combined,
            min_words=min_words,
            english_only=english_only,
            reject_emojis=reject_emojis,
            language_confidence_min=lang_min,
        )
        if not ok and reason:
            filter_stats[reason] += 1
            continue
        kept.append(r)

    deduped, dedupe_removed = dedupe_reviews(kept)

    max_reviews = int(ing.get("max_reviews", 0) or 0)
    capped_removed = 0
    if max_reviews > 0 and len(deduped) > max_reviews:
        deduped.sort(key=lambda r: r.review_date, reverse=True)
        capped_removed = len(deduped) - max_reviews
        deduped = deduped[:max_reviews]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for r in sorted(deduped, key=lambda x: (x.review_date, x.platform)):
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")

    by_platform = Counter(r.platform for r in deduped)
    by_rating = Counter(r.rating for r in deduped)
    dates = [r.review_date for r in deduped]

    summary: dict[str, Any] = {
        "as_of": as_of_d.isoformat(),
        "window_weeks": window_weeks,
        "files_loaded": files_loaded,
        "parsed_rows": len(all_parsed),
        "excluded_by_window": window_excluded,
        "excluded_by_filters": dict(filter_stats),
        "filter_rules": {
            "min_words": min_words,
            "english_only": english_only,
            "reject_emojis": reject_emojis,
        },
        "dedupe_removed": dedupe_removed,
        "capped_to_max_reviews": capped_removed,
        "max_reviews": max_reviews if max_reviews > 0 else None,
        "reviews_in_window_count": len(deduped),
        "by_platform": dict(by_platform),
        "by_rating": {str(k): v for k, v in sorted(by_rating.items())},
        "date_range": {
            "oldest": min(dates) if dates else None,
            "newest": max(dates) if dates else None,
        },
        "parse_errors": parse_errors,
        "output": str(output_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "warnings": [],
    }

    min_warn = int(ing.get("min_reviews_warn", 30))
    min_abort = int(ing.get("min_reviews_abort", 10))
    count = len(deduped)

    if count < min_warn:
        summary["warnings"].append(f"Low volume: {count} reviews (warn below {min_warn})")
    if count < min_abort:
        summary["abort_recommended"] = True
    else:
        summary["abort_recommended"] = False

    if dates:
        summary["week_gaps"] = _week_gaps(dates)

    summary_path = output_path.parent / "ingestion_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["summary_path"] = str(summary_path.relative_to(REPO_ROOT)).replace("\\", "/")

    return summary


def _week_gaps(dates_iso: list[str]) -> list[str]:
    """Weeks with zero reviews (informational)."""
    by_week: dict[str, int] = defaultdict(int)
    for d in dates_iso:
        dt = datetime.strptime(d, "%Y-%m-%d").date()
        label = dt.strftime("%G-W%V")
        by_week[label] += 1
    if len(by_week) < 2:
        return []
    return []
