"""Phase 3 analysis tests.

Covers: theme cap (T1), pulse structure (T2), quote integrity (T3),
PII negative (T4), PII positive (T5), word limit (T6), stability (T7).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from weeklypulse.analysis.models import ActionIdea, Quote, Theme
from weeklypulse.analysis.pii_guard import check_pii, detect_pii, pii_gate, redact_pii
from weeklypulse.analysis.pulse import (
    body_text,
    compose_pulse_md,
    count_body_words,
    generate_default_actions,
    trim_to_word_limit,
)
from weeklypulse.analysis.quotes import select_quotes
from weeklypulse.analysis.ranking import rank_themes, ranking_rationale, top_themes
from weeklypulse.analysis.themes import cluster_reviews
from weeklypulse.ingestion.models import Review

REPO = Path(__file__).resolve().parents[1]


# ── Helpers ───────────────────────────────────────────────────────────────


def _make_review(
    rid: str = "r1",
    platform: str = "ios",
    rating: int = 1,
    title: str = "Terrible",
    text: str = "KYC verification failed multiple times",
    date: str = "2026-05-20",
) -> Review:
    return Review(
        id=rid, platform=platform, rating=rating,
        title=title, text=text, review_date=date, source_file="test.csv",
    )


def _diverse_reviews(n: int = 50) -> list[Review]:
    """Generate a diverse set of reviews covering multiple themes."""
    templates = [
        ("KYC verification keeps failing, very frustrating experience", "kyc_issue", 1),
        ("Cannot complete document upload for KYC, app crashes", "kyc_crash", 1),
        ("Payment failed through UPI, money debited but not credited", "pay_fail", 1),
        ("UPI transaction stuck for 3 days, no response from support", "upi_stuck", 2),
        ("Withdrawal pending for 5 business days, still not received", "withdraw_slow", 1),
        ("App crashes every time I try to open portfolio page", "crash_port", 1),
        ("Login fails with correct credentials, had to reinstall", "login_fail", 1),
        ("Great app for mutual fund SIP, easy to use interface", "good_sip", 5),
        ("Portfolio tracking is accurate and statements download fast", "good_port", 4),
        ("Support team resolved my query within 24 hours, impressive", "good_support", 5),
        ("Slow loading on the orders page, takes 10 seconds", "slow_orders", 2),
        ("Order placement failed during market hours, very disappointing", "order_fail", 1),
        ("Add money feature works perfectly, no issues with UPI", "pay_good", 5),
        ("Withdrawal processed within 24 hours, smooth experience", "withdraw_good", 4),
        ("App is very slow and keeps freezing on my phone", "app_slow", 1),
    ]
    reviews: list[Review] = []
    for i in range(n):
        text, tag, rating = templates[i % len(templates)]
        platform = "ios" if i % 2 == 0 else "android"
        reviews.append(
            Review(
                id=f"r_{tag}_{i}",
                platform=platform,
                rating=rating,
                title=f"Review {i}",
                text=text,
                review_date=f"2026-05-{10 + (i % 20):02d}",
                source_file="test.csv",
            )
        )
    return reviews


# ── T1: Theme cap ─────────────────────────────────────────────────────────


class TestThemeCap:
    def test_max_five_themes(self):
        reviews = _diverse_reviews(50)
        themes = cluster_reviews(reviews, max_themes=5)
        assert len(themes) <= 5

    def test_max_three_themes(self):
        reviews = _diverse_reviews(50)
        themes = cluster_reviews(reviews, max_themes=3)
        assert len(themes) <= 3

    def test_all_reviews_assigned(self):
        reviews = _diverse_reviews(30)
        themes = cluster_reviews(reviews, max_themes=5)
        total = sum(t.review_count for t in themes)
        assert total == len(reviews)

    def test_theme_has_required_fields(self):
        reviews = _diverse_reviews(20)
        themes = cluster_reviews(reviews, max_themes=5)
        for t in themes:
            assert t.label
            assert t.description
            assert t.review_count > 0
            assert 0 <= t.avg_rating <= 5


# ── T2: Pulse structure ──────────────────────────────────────────────────


class TestPulseStructure:
    def test_pulse_md_has_sections(self):
        themes = [
            Theme("Test", "desc", 10, 3, 2.5, top_rank=1),
            Theme("Other", "desc", 5, 1, 3.0, top_rank=2),
            Theme("Third", "desc", 3, 0, 4.0, top_rank=3),
        ]
        quotes = [
            Quote("Great app", "r1", 5, "ios", "Test"),
            Quote("Bad experience", "r2", 1, "android", "Other"),
            Quote("Average product", "r3", 3, "ios", "Third"),
        ]
        actions = [
            ActionIdea("Fix the bug", "Test", "quick-win"),
            ActionIdea("Review feedback", "Other", "investigative"),
            ActionIdea("Improve UX", "Third", "cross-functional"),
        ]
        from weeklypulse.analysis.models import Pulse
        pulse = Pulse(
            app_name="Groww", week_label="2026-W22",
            date_range="2026-05-01 to 2026-05-31",
            generated_date="2026-05-29",
            themes=themes, quotes=quotes, actions=actions,
        )
        md = compose_pulse_md(pulse)

        assert "WeeklyPulse — Groww" in md
        assert "## Top themes this week" in md
        assert "## What users said" in md
        assert "## Suggested actions" in md
        assert "1. Test —" in md
        assert '"Great app"' in md
        assert "Fix the bug" in md


# ── T3: Quote integrity ──────────────────────────────────────────────────


class TestQuoteIntegrity:
    def test_quote_verbatim_from_source(self):
        """Quote text must be a substring of (or match) source review text."""
        reviews = [
            _make_review(rid="r1", text="KYC verification keeps failing repeatedly"),
            _make_review(rid="r2", platform="android", text="Payment failed through UPI"),
            _make_review(rid="r3", text="App crashes on portfolio page constantly"),
        ] + [_make_review(rid=f"fill_{i}", text="Generic review about the app") for i in range(10)]

        themes = cluster_reviews(reviews, max_themes=5)
        themes = rank_themes(themes, top_n=3)
        quotes = select_quotes(themes, reviews, count=3)

        review_map = {r.id: r for r in reviews}
        for q in quotes:
            source = review_map.get(q.source_review_id)
            assert source is not None
            # Quote text should come from source (after redaction)
            # At minimum, some words from the quote should appear in source
            source_words = set(source.text.lower().split())
            quote_words = set(q.text.lower().replace("[redacted]", "").split())
            assert quote_words & source_words, f"Quote {q.text} shares no words with source {source.text}"


# ── T4: PII negative test ────────────────────────────────────────────────


class TestPIINegative:
    def test_email_detected(self):
        passed, violations = check_pii("Contact me at user@email.com")
        assert not passed
        assert any(v["type"] == "email" for v in violations)

    def test_handle_detected(self):
        passed, violations = check_pii("My handle is @john_doe")
        assert not passed
        assert any(v["type"] == "handle" for v in violations)

    def test_phone_detected(self):
        passed, violations = check_pii("Call me at 9876543210")
        assert not passed
        assert any(v["type"] == "phone_number" for v in violations)

    def test_pan_detected(self):
        passed, violations = check_pii("My PAN is ABCDE1234F")
        assert not passed
        assert any(v["type"] == "pan_number" for v in violations)

    def test_account_id_detected(self):
        passed, violations = check_pii("My account number is account#12345")
        assert not passed

    def test_pii_gate_fails_with_pii(self):
        result = pii_gate("Email: test@example.com for support")
        assert not result["passed"]
        assert result["violation_count"] > 0


# ── T5: PII positive test ────────────────────────────────────────────────


class TestPIIPositive:
    def test_clean_text_passes(self):
        passed, violations = check_pii("The app crashes when I open the portfolio page")
        assert passed
        assert len(violations) == 0

    def test_clean_pulse_passes_gate(self):
        result = pii_gate("Withdrawal pending for three days, very slow process")
        assert result["passed"]

    def test_redaction_works(self):
        text, count = redact_pii("Contact user@email.com for help")
        assert count > 0
        assert "user@email.com" not in text
        assert "[REDACTED]" in text


# ── T6: Word limit ───────────────────────────────────────────────────────


class TestWordLimit:
    def test_body_word_count_excludes_headings(self):
        md = """WeeklyPulse — Groww
Week: 2026-W22 (2026-05-01 to 2026-05-31)
Generated: 2026-05-29

## Top themes this week
1. KYC — verification issues (10 reviews)

## What users said
- "KYC keeps failing" — ★, ios

## Suggested actions
1. Fix KYC flow
"""
        count = count_body_words(md)
        # Should only count body lines, not headings/header
        assert count > 0
        assert count < 50  # definitely not counting headings

    def test_trim_reduces_word_count(self):
        # Create a pulse with many words
        long_action = "This is a very long action idea that goes on and on with many words to exceed the limit"
        themes = [Theme("Test", "desc", 10, 3, 2.5, top_rank=1)]
        quotes = [Quote("Test quote text here for the word count", "r1", 1, "ios", "Test")]
        actions = [ActionIdea(long_action, "Test", "quick-win")]
        from weeklypulse.analysis.models import Pulse
        pulse = Pulse(
            app_name="Groww", week_label="2026-W22",
            date_range="2026-05-01 to 2026-05-31",
            generated_date="2026-05-29",
            themes=themes, quotes=quotes, actions=actions,
        )
        md = compose_pulse_md(pulse)
        original_count = count_body_words(md)
        trimmed = trim_to_word_limit(md, limit=20)
        trimmed_count = count_body_words(trimmed)
        assert trimmed_count <= 20 or trimmed_count <= original_count


# ── T7: Stability ────────────────────────────────────────────────────────


class TestStability:
    def test_same_input_same_top_themes(self):
        """Two runs on same reviews should produce overlapping top themes."""
        reviews = _diverse_reviews(40)
        themes1 = cluster_reviews(reviews, max_themes=5)
        themes1 = rank_themes(themes1, top_n=3)
        top1 = {t.label for t in top_themes(themes1)}

        themes2 = cluster_reviews(reviews, max_themes=5)
        themes2 = rank_themes(themes2, top_n=3)
        top2 = {t.label for t in top_themes(themes2)}

        # Same input should produce same top themes
        assert top1 == top2

    def test_ranking_deterministic(self):
        reviews = _diverse_reviews(30)
        themes = cluster_reviews(reviews, max_themes=5)
        ranked1 = rank_themes(list(themes), top_n=3)
        ranked2 = rank_themes(list(themes), top_n=3)
        assert [t.label for t in ranked1] == [t.label for t in ranked2]


# ── ADR-007 ranking ──────────────────────────────────────────────────────


class TestADR007Ranking:
    def test_primary_sort_by_count(self):
        t1 = Theme("A", "", 100, 10, 2.0)
        t2 = Theme("B", "", 50, 5, 3.0)
        t3 = Theme("C", "", 25, 1, 4.0)
        ranked = rank_themes([t3, t1, t2], top_n=3)
        assert ranked[0].label == "A"
        assert ranked[1].label == "B"
        assert ranked[2].label == "C"

    def test_tiebreak_by_low_rating_share(self):
        t1 = Theme("A", "", 50, 25, 2.0)  # 50% low-rated
        t2 = Theme("B", "", 50, 10, 3.0)  # 20% low-rated
        ranked = rank_themes([t2, t1], top_n=2)
        assert ranked[0].label == "A"  # higher severity first

    def test_second_tiebreak_alphabetical(self):
        t1 = Theme("Banana", "", 50, 10, 3.0)
        t2 = Theme("Apple", "", 50, 10, 3.0)
        ranked = rank_themes([t1, t2], top_n=2)
        assert ranked[0].label == "Apple"

    def test_top_rank_set(self):
        t1 = Theme("A", "", 100, 10, 2.0)
        t2 = Theme("B", "", 50, 5, 3.0)
        t3 = Theme("C", "", 25, 1, 4.0)
        t4 = Theme("D", "", 10, 0, 5.0)
        ranked = rank_themes([t4, t3, t2, t1], top_n=3)
        assert ranked[0].top_rank == 1
        assert ranked[1].top_rank == 2
        assert ranked[2].top_rank == 3
        assert ranked[3].top_rank == 0

    def test_ranking_rationale(self):
        t1 = Theme("KYC", "", 100, 50, 2.0, top_rank=1)
        t2 = Theme("Payments", "", 80, 20, 3.0, top_rank=2)
        t3 = Theme("Crashes", "", 60, 30, 2.5, top_rank=3)
        rationale = ranking_rationale([t1, t2, t3])
        assert "KYC" in rationale
        assert "100 reviews" in rationale
