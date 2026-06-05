# Phase 1 — MCP smoke test (run in Cursor Agent)

Run this in **Agent** mode with **Google Docs** and **Gmail** MCP tools enabled.

## Steps

1. **Google Docs MCP** — Create a document:
   - **Title:** `WeeklyPulse-MCP-Smoke`
   - **Body:** `WeeklyPulse smoke test. Production uses this MCP for weekly pulse delivery.`

2. **Gmail MCP** — Create a **draft** (do not send):
   - **To:** value from `.env` → `WEEKLYPULSE_DRAFT_TO`
   - **Subject:** `WeeklyPulse-MCP-Smoke`
   - **Body:** `WeeklyPulse MCP smoke test. See linked Doc if created.`

3. Record in [data/runs/smoke-mcp-notes.md](../data/runs/smoke-mcp-notes.md):
   - MCP server package names
   - Exact tool names used
   - Doc URL / id
   - Draft id
   - pass/fail

4. Confirm in Drive and Gmail **Drafts** UI.

## Alternative (API connectivity script)

If MCP tools are unavailable in a session, run once locally (browser OAuth):

```bash
.venv\Scripts\pip install google-auth-oauthlib google-api-python-client
.venv\Scripts\python scripts\phase1_smoke_google.py
```

This script is **not** part of `weeklypulse` (ADR-001); it only verifies Google access.
