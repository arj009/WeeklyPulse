"""App Store Connect review export parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from weeklypulse.ingestion.models import Review
from weeklypulse.ingestion.ids import make_review_id
from weeklypulse.ingestion.parsers.base import (
    build_header_map,
    parse_date,
    parse_rating,
    pick,
    read_csv_rows,
)

PLATFORM = "ios"

DATE_KEYS = ("review_date", "date", "created", "created_date")
RATING_KEYS = ("rating", "star_rating", "stars")
TITLE_KEYS = ("review_title", "title", "review_title")
TEXT_KEYS = ("review", "review_text", "body", "content", "text")


def detect(fieldnames: list[str]) -> bool:
    h = {x.lower() for x in fieldnames}
    if "package name" in h or "review link" in h:
        return False
    ios_hints = {"reviewer nickname", "app version", "country", "review title"}
    return bool(ios_hints & h) or ("rating" in h and "review" in h and "package name" not in h)


def parse_file(path: Path) -> tuple[list[Review], list[dict[str, Any]]]:
    fieldnames, rows = read_csv_rows(path)
    header_map = build_header_map(fieldnames)
    reviews: list[Review] = []
    errors: list[dict[str, Any]] = []

    for i, row in enumerate(rows, start=2):
        raw_date = pick(row, header_map, *DATE_KEYS)
        raw_rating = pick(row, header_map, *RATING_KEYS)
        title = pick(row, header_map, *TITLE_KEYS)
        text = pick(row, header_map, *TEXT_KEYS)

        d = parse_date(raw_date)
        rating = parse_rating(raw_rating)
        if d is None or rating is None:
            errors.append(
                {
                    "file": path.name,
                    "row": i,
                    "reason": "invalid_date_or_rating",
                }
            )
            continue

        review_date = d.isoformat()
        rid = make_review_id(PLATFORM, review_date, text, title)
        reviews.append(
            Review(
                id=rid,
                platform=PLATFORM,
                rating=rating,
                title=title,
                text=text,
                review_date=review_date,
                source_file=path.name,
            )
        )

    return reviews, errors
