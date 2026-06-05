"""Stable review identifiers."""

from __future__ import annotations

import hashlib


def make_review_id(platform: str, review_date: str, text: str, title: str) -> str:
    payload = f"{platform}|{review_date}|{title.strip()}|{text.strip()}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]
