# Agent vs pipeline responsibilities

Maps to [architecture.md](../docs/architecture.md) and **ADR-006**.

## Deterministic pipeline (implement in `src/weeklypulse/`)

| Step | Module (phase) | Responsibility |
|------|----------------|----------------|
| Layout / manifest template | `foundation` (1) | Paths, manifest schema |
| Parse exports | `ingestion` (2) | CSV/JSON → `reviews.jsonl` |
| Window filter | `ingestion` (2) | 8–12 weeks (default 10) |
| Dedupe | `ingestion` (2) | ADR-016 |
| Theme count ≤5 | `analysis` (3) | Enforce cap, merge if needed |
| Top-3 ranking | `analysis` (3) | ADR-007 rule |
| Word count ≤250 | `analysis` (3) | Body only, ADR-018 |
| PII gate | `analysis` (3) | Fail closed |
| Manifest write | `e2e` (5) | `data/runs/YYYY-Www/` |

## AI agent (Cursor + prompts)

| Step | Responsibility |
|------|----------------|
| Orchestration | Follow [weekly-run.md](./weekly-run.md) |
| Theme naming | Plain-language Groww-specific labels |
| Action ideas | Specific, PM-actionable items |
| Quote selection | Pick representative reviews (pipeline validates traceability) |
| MCP Docs | Full pulse to Google Doc |
| MCP Gmail | Teaser + link draft |
| Operator comms | Summary, warnings, next steps |

## Human operator

| Step | Responsibility |
|------|----------------|
| Export download | Weekly drop into `data/raw/` |
| MCP auth | Configure Cursor MCP (not in repo) |
| Send email | Review draft; send manually (ADR-010) |
| Stakeholder share | Forward Doc or sent mail |

## Stop / go matrix

| Condition | Agent action |
|-----------|--------------|
| Missing exports | STOP — list expected path |
| PII gate fail | STOP — no MCP |
| Ingest abort threshold | STOP — report count |
| Docs MCP fail | STOP Gmail if no URL; manifest `partial` |
| Gmail MCP fail | Doc ok; manifest `partial`; operator retry |
