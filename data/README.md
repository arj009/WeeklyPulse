# Data directory layout

WeeklyPulse stores all run data under `data/`. **Never commit raw exports** (`data/raw/` is gitignored).

## Where to see how much data you have

| What | Where | How to check |
|------|--------|----------------|
| **Downloaded exports** (original CSV) | `data/raw/` | File Explorer or `dir data\raw\*.csv` |
| **After ingest** (clean English reviews) | `data/processed/reviews.jsonl` | One JSON object per line |
| **Counts and filters** | `data/processed/ingestion_summary.json` | Open after `weeklypulse ingest` |
| **Sample / test only** | `data/fixtures/` | Not used unless you ingest that folder |

**Latest run (2026-05-30):** `data/raw/` has Groww CSVs (1000 Play + 500 iOS downloaded). After normalize: **463** reviews in `reviews.jsonl` (see `ingestion_summary.json`).

## Paths

| Path | Phase | Purpose |
|------|-------|---------|
| `raw/` | 2 | Operator drops App Store / Play Store export files |
| `processed/` | 2–3 | `reviews.jsonl`, `themes.json` |
| `output/` | 3–4 | `pulse.md`, `pulse.json` |
| `fixtures/` | 2 | Sanitized sample exports for tests (safe to commit) |
| `runs/` | 1+ | Per-week manifests: `runs/YYYY-Www/manifest.json` |

## Weekly run naming (ADR-011)

Use **ISO week** folders: `data/runs/2026-W22/`

Subject and Doc title use the same label: `WeeklyPulse — Groww — 2026-W22`

## Read / write by role

| Role | Reads | Writes |
|------|-------|--------|
| **Operator** | manifests, output | `raw/`, triggers runs |
| **Pipeline** | `raw/`, `processed/` | `processed/`, `output/`, `runs/` |
| **Agent** | config, prompts, pulse | MCP only for Google; manifest via pipeline |

See [architecture.md](../docs/architecture.md) and [config/README.md](../config/README.md).
