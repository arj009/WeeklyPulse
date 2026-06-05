"""Review normalization filters (ADR-020, ADR-021, ADR-022)."""

from __future__ import annotations

import re
from typing import Literal

# Broad emoji / pictograph ranges
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U00002700-\U000027BF"
    "\U000024C2-\U0001F251"
    "\u200d"
    "\ufe0f"
    "]",
    flags=re.UNICODE,
)

FilterReason = Literal[
    "too_few_words",
    "contains_emoji",
    "not_english",
    "language_unknown",
]


def word_count(text: str) -> int:
    return len(text.split())


def has_emoji(text: str) -> bool:
    return bool(EMOJI_PATTERN.search(text))


def meets_min_words(text: str, minimum: int) -> bool:
    return word_count(text) >= minimum


def is_english(text: str, min_confidence: float = 0.7) -> tuple[bool, str]:
    """
    Return (keep, reason). reason empty if keep.
  Uses langdetect; short texts may be ambiguous.
    """
    cleaned = text.strip()
    if not cleaned:
        return False, "too_few_words"

    try:
        from langdetect import DetectorFactory, detect_langs

        DetectorFactory.seed = 0
        langs = detect_langs(cleaned)
    except Exception:
        return False, "language_unknown"

    if not langs:
        return False, "language_unknown"

    best = langs[0]
    if best.lang == "en" and best.prob >= min_confidence:
        return True, ""
    if best.lang == "en" and best.prob < min_confidence:
        return False, "not_english"
    return False, "not_english"


def apply_content_filters(
    combined_text: str,
    *,
    min_words: int,
    english_only: bool,
    reject_emojis: bool,
    language_confidence_min: float,
) -> tuple[bool, FilterReason | None]:
    if reject_emojis and has_emoji(combined_text):
        return False, "contains_emoji"

    if not meets_min_words(combined_text, min_words):
        return False, "too_few_words"

    if english_only:
        keep, reason = is_english(combined_text, language_confidence_min)
        if not keep:
            return False, reason  # type: ignore[return-value]

    return True, None
