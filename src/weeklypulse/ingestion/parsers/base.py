"""Shared CSV parsing utilities."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Any


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            with path.open(encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise ValueError(f"No headers in {path}")
                fieldnames = [h.strip() for h in reader.fieldnames if h]
                rows = []
                for row in reader:
                    cleaned = {
                        (k or "").strip(): (v or "").strip()
                        for k, v in row.items()
                        if k is not None
                    }
                    if any(cleaned.values()):
                        rows.append(cleaned)
                return fieldnames, rows
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {path}")


def normalize_header(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def build_header_map(fieldnames: list[str]) -> dict[str, str]:
    return {normalize_header(f): f for f in fieldnames}


def pick(row: dict[str, str], header_map: dict[str, str], *candidates: str) -> str:
    for key in candidates:
        nk = normalize_header(key)
        if nk in header_map:
            val = row.get(header_map[nk], "").strip()
            if val:
                return val
    return ""


def parse_rating(raw: str) -> int | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        value = int(float(raw))
    except ValueError:
        return None
    if 1 <= value <= 5:
        return value
    return None


def parse_date(raw: str) -> date | None:
    raw = raw.strip()
    if not raw:
        return None
    formats = (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y/%m/%d",
    )
    for fmt in formats:
        try:
            return datetime.strptime(raw[:19], fmt).date()
        except ValueError:
            continue
    # ISO prefix
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")[:19]).date()
    except ValueError:
        return None
    return None
