"""Analysis data models (Phase 3)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Theme:
    """A single theme cluster."""

    label: str
    description: str
    review_count: int
    low_rating_count: int  # 1-2 star reviews
    avg_rating: float
    review_ids: list[str] = field(default_factory=list)
    top_rank: int = 0  # 1-3 if in pulse top 3, else 0

    @property
    def low_rating_share(self) -> float:
        """Share of 1-2 star reviews (ADR-007 tie-break)."""
        if self.review_count == 0:
            return 0.0
        return self.low_rating_count / self.review_count

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["low_rating_share"] = self.low_rating_share
        return d


@dataclass
class Quote:
    """A user quote extracted from a review."""

    text: str  # verbatim after PII redaction
    source_review_id: str
    source_rating: int
    source_platform: str
    theme_label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActionIdea:
    """A concrete action idea tied to a theme."""

    text: str
    theme_label: str
    kind: str = ""  # quick-win | investigative | cross-functional

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Pulse:
    """The weekly pulse document."""

    app_name: str
    week_label: str
    date_range: str
    generated_date: str
    themes: list[Theme]
    quotes: list[Quote]
    actions: list[ActionIdea]
    body_word_count: int = 0
    pii_gate: str = "not_run"  # not_run | pass | fail
    sentiment: dict[str, Any] = field(default_factory=dict)  # positive/negative/neutral percentages

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_name": self.app_name,
            "week_label": self.week_label,
            "date_range": self.date_range,
            "generated_date": self.generated_date,
            "themes": [t.to_dict() for t in self.themes],
            "quotes": [q.to_dict() for q in self.quotes],
            "actions": [a.to_dict() for a in self.actions],
            "body_word_count": self.body_word_count,
            "pii_gate": self.pii_gate,
            "sentiment": self.sentiment,
        }
