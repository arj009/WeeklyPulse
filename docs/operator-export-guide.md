# Operator guide — downloading store review exports

Place exported files in `data/raw/` before running ingest, **or** use the built-in public download:

```bash
python -m weeklypulse download -n 1000   # Play + App Store (public APIs)
python -m weeklypulse ingest
```

Manual CSV export from consoles is still supported (preferred for production compliance with ADR-002).

## Normalization rules (Phase 2)

Configured in `config/default.yaml` (see ADR-020–022):

| Rule | Default |
|------|---------|
| Minimum words (title + body combined) | **6** |
| Language | **English only** |
| Emojis | **Rejected** (row dropped) |
| Date window | **10 weeks** (8–12 allowed in config) |

Excluded rows are counted in `data/processed/ingestion_summary.json` under `excluded_by_filters`.

---

## Apple App Store (Groww iOS)

1. Sign in to [App Store Connect](https://appstoreconnect.apple.com/).
2. Open **Apps** → **Groww** → **Ratings and Reviews** (or Analytics → Reviews).
3. Export reviews as **CSV** for the desired date range (cover at least 8–12 weeks).
4. Save as e.g. `app_store_reviews.csv` in `data/raw/`.

**Expected columns** (names may vary): `Date`, `Rating`, `Review Title`, `Review`.

**Not imported into canonical data:** reviewer nickname, country, device identifiers.

---

## Google Play (Groww Android)

1. Sign in to [Google Play Console](https://play.google.com/console).
2. Select **Groww** → **Ratings and reviews** → **Reviews**.
3. Export reviews as **CSV**.
4. Save as e.g. `play_store_reviews.csv` in `data/raw/`.

**Expected columns:** `Review Submit Date and Time`, `Star Rating`, `Review Title`, `Review Text`, `Package Name`.

**Not imported:** reviewer name, device id, email, or other PII columns from export.

---

## After export

```bash
python -m weeklypulse config validate
python -m weeklypulse ingest
```

Review `data/processed/ingestion_summary.json` for counts and filter breakdown.

If `reviews_in_window_count` is below 10, ingestion recommends abort before analysis (ADR-017).
