# MCP smoke test notes (Phase 1)

Record results after running T3 in [phase-01-foundation eval](../../docs/phases/phase-01-foundation/eval.md). **Do not put secrets or OAuth tokens here.**

## Environment

| Field | Value |
|-------|-------|
| Date | 2026-05-30 |
| Cursor / host version | (operator) |
| Operator | Aunkar Ranjan |

## Google Docs MCP

| Field | Value |
|-------|-------|
| MCP server package name | _(fill after smoke — e.g. Google Workspace MCP)_ |
| Tool name(s) used | _(fill — e.g. create_document)_ |
| Test doc title | `WeeklyPulse-MCP-Smoke` |
| Result | pass / fail |
| Doc URL or id | _(fill after Agent smoke or phase1_smoke_google.py)_ |

## Gmail MCP

| Field | Value |
|-------|-------|
| MCP server package name | _(fill)_ |
| Tool name(s) used | _(fill — e.g. create_draft)_ |
| Test subject | `WeeklyPulse-MCP-Smoke` |
| Draft recipient | aunkarranjan@gmail.com |
| Result | pass / fail |
| Draft id (optional) | _(fill)_ |

## Confirmation

- [x] OAuth/credentials only in MCP host config — not committed in repo (use `.env` for draft_to only)
- [ ] Smoke doc visible in Drive
- [ ] Smoke draft visible in Gmail Drafts

## How to complete T3

**Option A — MCP (preferred):** Run [prompts/mcp-smoke-test.md](../../prompts/mcp-smoke-test.md) in Cursor Agent with Docs + Gmail MCP enabled.

**Option B — Local script:** Complete browser OAuth when prompted, then:

```bash
.venv\Scripts\python scripts\phase1_smoke_google.py
```

Paste `doc_url` and `draft_id` from script output above, then check confirmation boxes.

See [docs/mcp-setup.md](../../docs/mcp-setup.md).
