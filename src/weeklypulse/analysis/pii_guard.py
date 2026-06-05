"""PII detection and redaction gate (ADR-005, ADR-014).

Fail-closed: any detected PII blocks delivery.
"""

from __future__ import annotations

import re
from typing import Any


# --- Detection patterns ---------------------------------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_HANDLE_RE = re.compile(r"(?<!\w)@\w{2,}(?:\.\w+)*")
_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?"  # country code
    r"(?:\(?\d{2,4}\)?[\s.-]?)?"  # area
    r"\d{3,4}[\s.-]?\d{3,4}"  # main
    r"(?:[\s.-]?\d{1,4})?"  # extension
)
_ACCOUNT_ID_RE = re.compile(
    r"(?:(?:account|user|customer|client|order|ref|ticket|transaction)"
    r"[\s]*[:#]\s*"  # require separator like ":" or "#" after the label
    r"\d[\w-]{2,})",  # ID must start with a digit
    re.IGNORECASE,
)
_PAN_RE = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")  # Indian PAN format
_AADHAAR_RE = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")  # 12-digit
_UPI_RE = re.compile(r"\b\w+@\w+\b")  # UPI ID like name@bank

# Ordered by severity — checked first
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", _EMAIL_RE),
    ("pan_number", _PAN_RE),
    ("aadhaar_number", _AADHAAR_RE),
    ("phone_number", _PHONE_RE),
    ("handle", _HANDLE_RE),
    ("account_id", _ACCOUNT_ID_RE),
]


def detect_pii(text: str) -> list[dict[str, Any]]:
    """Return list of PII violations found in *text*.

    Each violation: ``{"type": str, "match": str, "start": int, "end": int}``.
    """
    violations: list[dict[str, Any]] = []
    seen_spans: set[tuple[int, int]] = set()

    for pii_type, pattern in _PII_PATTERNS:
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            # Skip overlapping matches already captured by a higher-priority rule
            if any(s <= span[0] < e for s, e in seen_spans):
                continue
            seen_spans.add(span)
            violations.append(
                {
                    "type": pii_type,
                    "match": m.group(),
                    "start": m.start(),
                    "end": m.end(),
                }
            )

    # Post-filter: remove UPI false positives that overlap with email matches
    violations = _filter_upi_false_positives(text, violations)

    return violations


def _filter_upi_false_positives(
    text: str, violations: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Remove UPI-style matches that overlap with email matches."""
    email_spans = {
        (v["start"], v["end"]) for v in violations if v["type"] == "email"
    }
    return [
        v
        for v in violations
        if not (
            v["type"] == "upi_id"
            and any(
                es <= v["start"] < ee or es < v["end"] <= ee
                for es, ee in email_spans
            )
        )
    ]


def check_pii(text: str) -> tuple[bool, list[dict[str, Any]]]:
    """Run PII gate on *text*.

    Returns ``(pass_flag, violations)``.
    Fail-closed: any violation → fail.
    """
    violations = detect_pii(text)
    return len(violations) == 0, violations


def redact_pii(text: str, replacement: str = "[REDACTED]") -> tuple[str, int]:
    """Redact detected PII in *text*, replacing with *replacement*.

    Returns ``(redacted_text, redaction_count)``.
    """
    violations = detect_pii(text)
    if not violations:
        return text, 0

    # Replace from end to preserve earlier indices
    result = text
    for v in sorted(violations, key=lambda v: v["start"], reverse=True):
        result = result[: v["start"]] + replacement + result[v["end"] :]

    return result, len(violations)


def pii_gate(text: str) -> dict[str, Any]:
    """Full PII gate suitable for pipeline integration.

    Returns dict with keys: ``passed``, ``violations``, ``redacted_text``.
    """
    violations = detect_pii(text)
    passed = len(violations) == 0
    redacted, count = redact_pii(text)

    return {
        "passed": passed,
        "violation_count": len(violations),
        "violations": [
            {"type": v["type"], "match": v["match"]} for v in violations
        ],
        "redacted_text": redacted,
        "redaction_count": count,
    }
