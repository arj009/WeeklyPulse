"""Theme clustering engine (Phase 3, Activity 3.2).

Groups reviews into ≤5 themes using Groww-domain keyword matching,
then optionally uses Groq LLM to refine theme labels and descriptions
(ADR-006: agent-assisted synthesis).
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

from weeklypulse.analysis.models import Theme
from weeklypulse.ingestion.models import Review

logger = logging.getLogger(__name__)

# Groww-specific keyword map (from architecture § Groww-specific analysis context)
# Each key is a canonical theme slug; values are regex patterns (case-insensitive).
THEME_KEYWORDS: dict[str, list[str]] = {
    "onboarding_kyc": [
        r"\bkyc\b",
        r"\bverif",
        r"\bonboard",
        r"\bdocument\s*upload",
        r"\bpan\b",
        r"\baadhaar?",
        r"\bidentity",
        r"\bsign[\s-]?up\b",
        r"\bregistration",
        r"\bopen\s*account",
    ],
    "payments_upi": [
        r"\bpayment\b",
        r"\bupi\b",
        r"\btransaction\b",
        r"\bmandate\b",
        r"\bbank\s*link",
        r"\bdeposit",
        r"\badd\s*money",
        r"\bfund\s*add",
        r"\bpay\b",
        r"\bneft\b",
        r"\bimps\b",
    ],
    "portfolio_statements": [
        r"\bportfolio\b",
        r"\bstatement\b",
        r"\bholding",
        r"\bbalance\b",
        r"\btax\b",
        r"\bp&l\b",
        r"\bprofit\b",
        r"\bloss\b",
        r"\bnav\b",
        r"\bxirr\b",
        r"\bcagr\b",
    ],
    "withdrawals": [
        r"\bwithdraw",
        r"\bwithdrawal",
        r"\bcredit\b",
        r"\bpayout\b",
        r"\bmoney\s*back",
        r"\brefund\b",
        r"\bredeem",
    ],
    "trading_orders": [
        r"\border\b",
        r"\btrade\b",
        r"\bbuy\b",
        r"\bsell\b",
        r"\bslippage\b",
        r"\bmarket\b",
        r"\bstock\b",
        r"\bmutual\s*fund\b",
        r"\bmf\b",
        r"\bsip\b",
        r"\bipo\b",
    ],
    "app_quality": [
        r"\bcrash",
        r"\blogin\b",
        r"\blog\s*in\b",
        r"\bnotification",
        r"\bslow\b",
        r"\bloading\b",
        r"\bbug\b",
        r"\bupdate\b",
        r"\bfreeze",
        r"\bhang",
        r"\berror\b",
        r"\bglitch",
        r"\blag",
        r"\bsign\s*in\b",
        r"\boot\b",
    ],
    "support": [
        r"\bsupport\b",
        r"\bcustomer\s*care",
        r"\bcallback\b",
        r"\bticket\b",
        r"\bchat\b",
        r"\bcomplaint\b",
        r"\bhelp\s*desk",
        r"\bno\s*response",
        r"\bresolve",
        r"\bunresolved",
    ],
}

# Human-readable labels for slug → display
THEME_LABELS: dict[str, str] = {
    "onboarding_kyc": "Onboarding & KYC",
    "payments_upi": "Payments & UPI",
    "portfolio_statements": "Portfolio & Statements",
    "withdrawals": "Withdrawals",
    "trading_orders": "Trading & Orders",
    "app_quality": "App Quality",
    "support": "Customer Support",
    "other": "Other Feedback",
}

THEME_DESCRIPTIONS: dict[str, str] = {
    "onboarding_kyc": "Issues with account creation, KYC verification, and document uploads",
    "payments_upi": "Problems with payments, UPI transactions, deposits, and bank linking",
    "portfolio_statements": "Concerns about portfolio display, statements, tax documents, and P&L",
    "withdrawals": "Complaints about withdrawal delays, failed payouts, and refund issues",
    "trading_orders": "Issues with order placement, trade execution, SIP, and mutual fund flows",
    "app_quality": "App crashes, login problems, slow performance, and bugs",
    "support": "Customer support responsiveness, unresolved tickets, and communication quality",
    "other": "Feedback not matching specific product areas",
}

# Compile patterns once
_COMPILED: dict[str, list[re.Pattern[str]]] = {
    slug: [re.compile(p, re.IGNORECASE) for p in patterns]
    for slug, patterns in THEME_KEYWORDS.items()
}


def _assign_theme(review: Review) -> str:
    """Return the best-matching theme slug for a review.

    Picks the theme with the most keyword hits.
    Ties broken by first match (deterministic iteration order).
    Returns 'other' if no keywords match.
    """
    best_slug = "other"
    best_count = 0

    text = review.combined_text()
    for slug, patterns in _COMPILED.items():
        count = sum(1 for p in patterns if p.search(text))
        if count > best_count:
            best_count = count
            best_slug = slug

    return best_slug


def cluster_reviews(reviews: list[Review], max_themes: int = 5) -> list[Theme]:
    """Cluster reviews into ≤ *max_themes* themes.

    1. Assign each review to a keyword-matched theme.
    2. If more than *max_themes* themes have reviews, merge smallest.
    3. Build Theme objects with counts and ratings.

    Returns themes sorted by review_count descending (ranked later by ADR-007).
    """
    # --- assign ---
    assignment: dict[str, list[Review]] = {}
    for r in reviews:
        slug = _assign_theme(r)
        assignment.setdefault(slug, []).append(r)

    # --- merge if > max_themes ---
    if len(assignment) > max_themes:
        assignment = _merge_smallest(assignment, max_themes)

    # --- build Theme objects ---
    themes: list[Theme] = []
    for slug, revs in assignment.items():
        low_count = sum(1 for r in revs if r.rating <= 2)
        avg_rating = sum(r.rating for r in revs) / len(revs) if revs else 0.0

        themes.append(
            Theme(
                label=THEME_LABELS.get(slug, slug),
                description=THEME_DESCRIPTIONS.get(slug, ""),
                review_count=len(revs),
                low_rating_count=low_count,
                avg_rating=round(avg_rating, 2),
                review_ids=[r.id for r in revs],
            )
        )

    # Sort by review_count descending (pre-ranking order)
    themes.sort(key=lambda t: t.review_count, reverse=True)
    return themes


def _merge_smallest(
    assignment: dict[str, list[Review]], max_themes: int
) -> dict[str, list[Review]]:
    """Merge smallest-themed groups into 'other' until count ≤ *max_themes*.

    Iteratively moves reviews from the smallest non-other theme into
    the 'other' bucket until the total theme count is within cap.
    """
    while len(assignment) > max_themes:
        # Find the smallest non-"other" theme
        candidates = [s for s in assignment if s != "other"]
        if not candidates:
            break
        smallest_slug = min(candidates, key=lambda s: len(assignment[s]))
        # Move its reviews to "other"
        other_reviews = assignment.setdefault("other", [])
        other_reviews.extend(assignment.pop(smallest_slug))

    # Remove 'other' if empty
    if "other" in assignment and not assignment["other"]:
        del assignment["other"]

    return assignment


def get_theme_distribution(themes: list[Theme]) -> dict[str, int]:
    """Return ``{theme_label: review_count}`` for reporting."""
    return {t.label: t.review_count for t in themes}


def refine_themes_with_llm(
    themes: list[Theme],
    reviews: list[Review],
    model: str = "llama-3.3-70b-versatile",
) -> list[Theme]:
    """Use Groq LLM to relabel themes based on actual review content.

    Keeps the deterministic clustering and stats intact — only replaces
    the label and description with LLM-generated ones.

    Falls back to existing labels if LLM fails.
    """
    from weeklypulse.analysis.llm import label_themes_with_llm

    review_map = {r.id: r for r in reviews}

    # Build sample reviews per theme for the LLM
    theme_data: list[dict[str, Any]] = []
    slug_map: dict[str, str] = {}  # original_slug → theme index

    for i, t in enumerate(themes):
        # Recover the slug from the original assignment
        # We use the label to find a matching slug
        slug = _label_to_slug(t.label)
        slug_map[slug] = str(i)

        # Get sample review texts
        samples: list[str] = []
        for rid in t.review_ids[:10]:
            rev = review_map.get(rid)
            if rev:
                text = rev.combined_text()
                if len(text) > 20:
                    samples.append(text[:200])  # truncate long reviews

        theme_data.append({
            "slug": slug,
            "review_count": t.review_count,
            "sample_reviews": samples,
        })

    llm_labels = label_themes_with_llm(theme_data, model=model)

    if not llm_labels:
        logger.warning("LLM theme labeling failed; keeping deterministic labels")
        return themes

    # Apply LLM labels
    for slug, info in llm_labels.items():
        idx_str = slug_map.get(slug)
        if idx_str is not None:
            idx = int(idx_str)
            if idx < len(themes):
                themes[idx].label = info.get("label", themes[idx].label)
                themes[idx].description = info.get("description", themes[idx].description)

    return themes


def _label_to_slug(label: str) -> str:
    """Reverse-lookup: convert a display label back to its slug."""
    for slug, lbl in THEME_LABELS.items():
        if lbl == label:
            return slug
    # Fallback: normalize the label
    return label.lower().replace(" & ", "_").replace(" ", "_").replace("&", "_")
