"""Detect export format and parse."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from weeklypulse.ingestion.models import Review
from weeklypulse.ingestion.parsers import app_store, play_store
from weeklypulse.ingestion.parsers.base import read_csv_rows


def parse_export_file(path: Path) -> tuple[list[Review], list[dict[str, Any]], str]:
    if path.suffix.lower() not in {".csv", ".tsv", ".txt"}:
        raise ValueError(f"Unsupported file type: {path.name}")

    fieldnames, _ = read_csv_rows(path)
    if play_store.detect(fieldnames):
        reviews, errors = play_store.parse_file(path)
        return reviews, errors, "android"
    if app_store.detect(fieldnames):
        reviews, errors = app_store.parse_file(path)
        return reviews, errors, "ios"
    # Fallback: try play then app
    reviews, errors = play_store.parse_file(path)
    if reviews:
        return reviews, errors, "android"
    reviews, errors = app_store.parse_file(path)
    return reviews, errors, "ios"
