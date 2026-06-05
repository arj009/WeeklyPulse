# Phase 2 — Ingestion — Evaluation

**Phase goal:** Public App Store and Play Store exports → single normalized, in-window review dataset ready for analysis.

**Reference:** [Implementation plan — Phase 2](../../phase-wise-implementation-plan.md#phase-2--ingestion)

**Prerequisite:** Phase 1 eval passed (MCP smoke deferred by operator).

**Completed:** 2026-05-30 — Downloaded Groww reviews via `weeklypulse download`, ingested to `reviews.jsonl` (**463** reviews after filters).

---

## Activity checklist

| Activity | Description | Done? |
|----------|-------------|-------|
| **2.1** | Obtain and classify source files | ☑ |
| **2.2** | Define canonical review record | ☑ |
| **2.3** | Normalize and merge | ☑ |
| **2.4** | Apply time window | ☑ |
| **2.5** | Quality checks and ingestion report | ☑ |
| **2.6** | Operator playbook (export refresh) | ☑ |

---

## Exit criteria (by activity)

### Activity 2.1 — Obtain and classify source files

| # | Criterion | Pass? |
|---|-----------|-------|
| 2.1a | Representative **App Store** export(s) for Groww obtained | ☑ `data/raw/app_store_reviews.csv` (500) |
| 2.1b | Representative **Play Store** export(s) for Groww obtained | ☑ `data/raw/play_store_reviews.csv` (1000) |
| 2.1c | Format documented: file type, columns, date format, encoding | ☑ CSV UTF-8 |
| 2.1d | Required fields identified: rating, title, text, date, platform | ☑ |
| 2.1e | PII-bearing export fields excluded from canonical schema | ☑ |

### Activity 2.2 — Canonical review record

| # | Criterion | Pass? |
|---|-----------|-------|
| 2.2a | One record shape for all platforms | ☑ |
| 2.2b | Stable `id` rule documented | ☑ ADR-016 / `ids.py` |
| 2.2c | Rules for empty title/text documented | ☑ |
| 2.2d | Non-English reviews **excluded** (ADR-020) | ☑ 40 dropped |
| 2.2f | Fewer than 6 words excluded (ADR-021) | ☑ 824 dropped |
| 2.2g | Emojis excluded (ADR-022) | ☑ 172 dropped |
| 2.2e | Platform tags: `ios` and `android` | ☑ |

### Activity 2.3 — Normalize and merge

| # | Criterion | Pass? |
|---|-----------|-------|
| 2.3a | App Store export parses | ☑ |
| 2.3b | Play Store export parses | ☑ |
| 2.3c | iOS + Android merged | ☑ |
| 2.3d | Deduplication applied (ADR-016) | ☑ |
| 2.3e | Unparseable rows logged | ☑ |

### Activity 2.4 — Apply time window

| # | Criterion | Pass? |
|---|-----------|-------|
| 2.4a | “As of” date rule documented | ☑ run date / `--as-of` |
| 2.4b | Only reviews within 8–12 week window | ☑ 10 weeks |
| 2.4c | Report includes date stats | ☑ `ingestion_summary.json` |

### Activity 2.5 — Quality checks and ingestion report

| # | Criterion | Pass? |
|---|-----------|-------|
| 2.5a | `data/processed/reviews.jsonl` written | ☑ **463** reviews |
| 2.5b | Summary by platform, rating | ☑ |
| 2.5c | Warn below minimum | ☑ no warn (463 > 30) |
| 2.5d | Date gaps flagged | ☑ |
| 2.5e | Summary ready for manifest | ☑ |

### Activity 2.6 — Operator playbook

| # | Criterion | Pass? |
|---|-----------|-------|
| 2.6a | App Store download steps | ☑ [operator-export-guide.md](../../operator-export-guide.md) |
| 2.6b | Play Store download steps | ☑ |
| 2.6c | Place files in `data/raw/` | ☑ |
| 2.6d | Refresh cadence documented | ☑ |

---

## Run evidence (2026-05-30)

```text
weeklypulse download -n 1000  → Play 1000, iOS 500 (RSS page limit)
weeklypulse ingest            → 463 reviews retained
  ios: 245, android: 218
  filters: too_few_words 824, emoji 172, not_english 40
```

---

## Sign-off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Implementer | Cursor agent | 2026-05-30 | ☑ |
| Operator | | | ☐ |

**Phase 2 status:** ☑ **Passed** (ready for Phase 3)
