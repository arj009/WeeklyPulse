"""Phase 2 ingestion tests."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from weeklypulse.config import load_config
from weeklypulse.ingestion.filters import (
    apply_content_filters,
    has_emoji,
    meets_min_words,
)
from weeklypulse.ingestion.ids import make_review_id
from weeklypulse.ingestion.parsers.registry import parse_export_file
from weeklypulse.ingestion.pipeline import run_ingestion

FIXTURES = Path(__file__).resolve().parents[1] / "data" / "fixtures"
REPO = Path(__file__).resolve().parents[1]


def test_word_count_minimum():
    assert meets_min_words("one two three four five", 6) is False
    assert meets_min_words("one two three four five six", 6) is True


def test_emoji_detection():
    assert has_emoji("hello 😀 world") is True
    assert has_emoji("hello world") is False


def test_english_filter():
    ok, reason = apply_content_filters(
        "This is a clear English review about payments and withdrawals today.",
        min_words=6,
        english_only=True,
        reject_emojis=True,
        language_confidence_min=0.7,
    )
    assert ok is True
    assert reason is None

    ok, reason = apply_content_filters(
        "Esta aplicación es muy buena y fácil de usar para invertir dinero.",
        min_words=6,
        english_only=True,
        reject_emojis=True,
        language_confidence_min=0.7,
    )
    assert ok is False
    assert reason == "not_english"


def test_stable_review_id():
    a = make_review_id("ios", "2026-05-01", "same text", "title")
    b = make_review_id("ios", "2026-05-01", "same text", "title")
    assert a == b


def test_parse_app_store_fixture():
    path = FIXTURES / "app_store_sample.csv"
    reviews, errors, platform = parse_export_file(path)
    assert platform == "ios"
    assert len(reviews) >= 4
    assert all(r.platform == "ios" for r in reviews)


def test_parse_play_store_fixture():
    path = FIXTURES / "play_store_sample.csv"
    reviews, errors, platform = parse_export_file(path)
    assert platform == "android"
    assert len(reviews) >= 4


def test_ingestion_pipeline_with_filters(tmp_path):
    cfg = load_config()
    cfg = dict(cfg)
    cfg["ingestion"] = dict(cfg["ingestion"])
    cfg["ingestion"]["processed_output"] = "data/processed/test_reviews.jsonl"

    raw = tmp_path / "raw"
    raw.mkdir()
    for name in ("app_store_sample.csv", "play_store_sample.csv"):
        (raw / name).write_text(
            (FIXTURES / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    summary = run_ingestion(cfg, input_dir=raw, as_of="2026-05-29")

    assert summary["reviews_in_window_count"] >= 2
    assert summary["excluded_by_window"] >= 1
    filters = summary["excluded_by_filters"]
    assert filters.get("too_few_words", 0) >= 1
    assert filters.get("contains_emoji", 0) >= 1
    assert filters.get("not_english", 0) >= 1

    out = REPO / "data/processed/test_reviews.jsonl"
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        row = json.loads(line)
        assert row["platform"] in ("ios", "android")
        assert 1 <= row["rating"] <= 5
        text = f"{row['title']} {row['text']}".strip()
        assert not has_emoji(text)
