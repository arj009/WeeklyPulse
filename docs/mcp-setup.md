# MCP setup — Google Docs and Gmail

WeeklyPulse uses **MCP servers only** for Google (ADR-001). Credentials stay in your **Cursor MCP configuration**, not in this repository.

## Prerequisites

- Cursor (or compatible host) with MCP support
- Google account with Drive and Gmail access
- Phase 1 eval activity **1.3** smoke tests completed

## Configure in Cursor

1. Open **Cursor Settings → MCP** (or edit MCP config file for your install).
2. Add your chosen **Google Docs** and **Gmail** MCP server packages.
3. Complete OAuth in the browser when prompted.
4. Restart Cursor if tools do not appear.

> **Note:** Exact package names depend on your environment. Common patterns include community Google Workspace MCP servers. Record the tools you use in [data/runs/smoke-mcp-notes.md](../data/runs/smoke-mcp-notes.md).

## Expected tool contracts

Document **your** tool names after smoke test. Intended behavior:

### Google Docs MCP

| Intent | Typical inputs | Expected return |
|--------|----------------|-----------------|
| Create or update weekly doc | `title`, `body` (markdown or plain text) | `doc_id`, `doc_url` |

- Title pattern: `WeeklyPulse — Groww — YYYY-Www` (from config).
- Body: full `pulse.md` content after PII pass.

### Gmail MCP

| Intent | Typical inputs | Expected return |
|--------|----------------|-----------------|
| Create draft | `to`, `subject`, `body` | `draft_id` |

- `to`: `WEEKLYPULSE_DRAFT_TO` from `.env`
- Subject: same week label as doc
- Body: short teaser + link to Doc (ADR-008)

## Smoke test procedure

1. Create doc titled **`WeeklyPulse-MCP-Smoke`** via Docs MCP.
2. Create draft to self, subject **`WeeklyPulse-MCP-Smoke`**, body `MCP smoke test`.
3. Verify in Drive and Gmail Drafts.
4. Fill in [data/runs/smoke-mcp-notes.md](../data/runs/smoke-mcp-notes.md).

## Security

- Do **not** commit OAuth tokens, `credentials.json`, or `.env`.
- Use least-privilege scopes required for create doc + create draft.
- Only pass **PII-scrubbed** pulse text to MCP tools.

## Delivery sequence (ADR-013)

```text
PII gate pass → Docs MCP → capture URL → Gmail MCP (teaser + link) → manifest
```

## Troubleshooting

| Issue | Action |
|-------|--------|
| Tools not listed | Restart Cursor; check MCP server logs |
| Auth expired | Re-authenticate in MCP settings |
| Doc ok, draft fails | Manifest `partial`; retry Gmail only |
| PII gate failed | Fix pulse locally; do not call MCP |

See [architecture.md](./architecture.md) and [phase-04 eval](./phases/phase-04-delivery-mcp/eval.md).
