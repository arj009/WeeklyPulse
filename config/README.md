# Configuration

WeeklyPulse reads **`config/default.yaml`** by default. Operators change behavior here—**not** by editing agent prompts in `prompts/`.

## Quick overrides

| What to change | Key path | Example |
|----------------|----------|---------|
| Review lookback | `ingestion.review_window_weeks` | `10` (allowed 8–12) |
| Gmail draft recipient | `delivery.draft_to` or env `WEEKLYPULSE_DRAFT_TO` | `you@company.com` |
| Theme / word limits | `analysis.*` | See default.yaml |
| Raw export folder | `ingestion.raw_input_dir` | `data/raw` |
| Min words per review | `ingestion.min_words` | `6` |
| English only | `ingestion.english_only` | `true` |
| Reject emojis | `ingestion.reject_emojis` | `true` |
| Max reviews kept | `ingestion.max_reviews` | `1000` (newest first; `0` = unlimited) |

## Environment variables

| Variable | Purpose |
|----------|---------|
| `WEEKLYPULSE_CONFIG` | Path to alternate YAML file |
| `WEEKLYPULSE_DRAFT_TO` | Gmail draft recipient (kept out of git) |

Copy `.env.example` to `.env` locally (never commit `.env`).

## Validate config

```bash
python -m weeklypulse config validate
```

## Related decisions

- ADR-012 — default 10-week window  
- ADR-008 — Doc canonical, email teaser + link  
- ADR-011 — ISO week run folders  

See [docs/decision.md](../docs/decision.md).
