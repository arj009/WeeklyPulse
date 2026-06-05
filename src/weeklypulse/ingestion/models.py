"""Canonical review model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Review:
    id: str
    platform: str  # ios | android
    rating: int
    title: str
    text: str
    review_date: str  # YYYY-MM-DD
    source_file: str

    def combined_text(self) -> str:
        parts = [self.title.strip(), self.text.strip()]
        return " ".join(p for p in parts if p)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
