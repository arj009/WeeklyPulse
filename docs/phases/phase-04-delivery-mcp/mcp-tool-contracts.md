# MCP Tool Contracts — WeeklyPulse Google Services

**Server:** `weeklypulse.delivery.mcp_google_server`  
**Protocol:** MCP (Model Context Protocol) via FastMCP  
**Version:** 1.0.0

This document defines the exact tool contracts for the WeeklyPulse MCP server that integrates with Google Docs and Gmail.

---

## Server Information

- **Server Name:** `WeeklyPulse Google Services`
- **Entry Point:** `python -m weeklypulse.delivery.mcp_google_server`
- **Authentication:** Google OAuth2 (automatic token refresh)
- **Scopes Required:**
  - `https://www.googleapis.com/auth/documents`
  - `https://www.googleapis.com/auth/gmail.compose`
  - `https://www.googleapis.com/auth/drive.readonly`

---

## Tool 1: `create_or_update_doc`

Creates or updates a Google Doc with weekly pulse content.

### Idempotency (ADR-019)

This tool is **idempotent**: if a document with the same `title` already exists in Google Drive (not trashed), it will **update** the existing document rather than creating a duplicate.

### Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | Document title. Pattern: `WeeklyPulse — {app} — {week_label}` (e.g., `WeeklyPulse — Groww — 2026-W22`) |
| `body` | string | Yes | Full pulse content in markdown format (after PII gate pass) |
| `week_label` | string | No | ISO week label for tracking (e.g., `2026-W22`) |

### Returns

**Success:**
```json
{
  "doc_id": "1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT",
  "doc_url": "https://docs.google.com/document/d/1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT/edit",
  "action": "created",
  "title": "WeeklyPulse — Groww — 2026-W22"
}
```

**Update (idempotent):**
```json
{
  "doc_id": "1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT",
  "doc_url": "https://docs.google.com/document/d/1aB2cD3eF4gH5iJ6kL7mN8oP9qR0sT/edit",
  "action": "updated",
  "title": "WeeklyPulse — Groww — 2026-W22"
}
```

**Error:**
```json
{
  "error": "Failed to create/update doc: <error details>"
}
```

### Failure Modes

| Error Type | Cause | Resolution |
|------------|-------|------------|
| `FileNotFoundError` | `Credential.json` not found | Download OAuth credentials from Google Cloud Console |
| `HttpError (401)` | OAuth token expired or invalid | Delete `token.json` and re-authenticate |
| `HttpError (403)` | Insufficient permissions | Verify OAuth scopes in Google Cloud Console |
| `HttpError (429)` | Google API quota exceeded | Wait and retry; implement exponential backoff |
| `RuntimeError` | Google Docs API error | Check error message for details; verify document access |

### Content Formatting

- Markdown headings (`#`, `##`, `###`) are converted to plain text
- Bold/italic markers (`**`, `*`) are stripped
- Future enhancement: use Google Docs rich text formatting requests

---

## Tool 2: `create_draft`

Creates a Gmail draft for the weekly pulse email (draft-only per ADR-010).

### Draft-Only Policy (ADR-010)

This tool **only creates drafts**. The human operator must review and manually send the email from Gmail.

### Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | string | Yes | Recipient email address (from `WEEKLYPULSE_DRAFT_TO` in `.env`) |
| `subject` | string | Yes | Email subject. Pattern: `WeeklyPulse — {app} — {week_label}` |
| `body` | string | Yes | Email body text (teaser content, not full pulse) |
| `doc_url` | string | No | Link to Google Doc (appended to body per ADR-008) |

### Returns

**Success:**
```json
{
  "draft_id": "r-1234567890",
  "to": "user@example.com",
  "subject": "WeeklyPulse — Groww — 2026-W22"
}
```

**Error:**
```json
{
  "error": "Failed to create draft: <error details>"
}
```

### Email Composition (ADR-008)

Per ADR-008 (Doc canonical; email teaser + link), the email body is composed as:

```
{body}

View full pulse in Google Docs: {doc_url}
```

If `doc_url` is not provided, the link is omitted.

### Failure Modes

| Error Type | Cause | Resolution |
|------------|-------|------------|
| `FileNotFoundError` | `Credential.json` not found | Download OAuth credentials from Google Cloud Console |
| `HttpError (401)` | OAuth token expired or invalid | Delete `token.json` and re-authenticate |
| `HttpError (403)` | Insufficient permissions | Verify Gmail API is enabled in Google Cloud Console |
| `HttpError (429)` | Gmail API quota exceeded | Wait and retry; implement exponential backoff |
| `RuntimeError` | Gmail API error | Check error message; verify Gmail account access |

---

## Delivery Sequence (ADR-013)

The correct order for delivering a weekly pulse is:

```
1. PII gate pass (verify pulse.md has no PII)
2. Call create_or_update_doc with full pulse content
3. Capture doc_url from response
4. Call create_draft with teaser + doc_url
5. Update manifest.json with delivery status
6. Notify operator to review and send draft
```

**Important:** Always call `create_or_update_doc` **before** `create_draft` to ensure the doc link is available for the email.

---

## Testing

### Test Mode

The server includes a test mode for direct tool invocation without running the MCP server:

```bash
# Test Google Docs
python -m weeklypulse.delivery.mcp_google_server --test test-docs \
  --title "Test Pulse" \
  --body "# Test Content\n\nThis is a test."

# Test Gmail
python -m weeklypulse.delivery.mcp_google_server --test test-gmail \
  --to "user@example.com" \
  --subject "Test Pulse" \
  --body "This is a test email."
```

### Expected Behavior

- **First run:** Browser opens for OAuth authentication
- **Subsequent runs:** Token automatically refreshed from `token.json`
- **Test mode:** Outputs result to console instead of returning via MCP

---

## Security Considerations

1. **Credentials:** `Credential.json` and `token.json` are excluded from version control (see `.gitignore`)
2. **Scopes:** Minimum required scopes are used (docs, gmail.compose, drive.readonly)
3. **PII:** Only PII-scrubbed content should be passed to these tools
4. **Token Storage:** `token.json` is stored in project root with restricted access

---

## Integration Example

### Python Agent Integration

```python
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def deliver_pulse(pulse_md: str, week_label: str, recipient: str):
    """Deliver weekly pulse via MCP server."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "weeklypulse.delivery.mcp_google_server"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Step 1: Create/update doc
            doc_result = await session.call_tool(
                "create_or_update_doc",
                arguments={
                    "title": f"WeeklyPulse — Groww — {week_label}",
                    "body": pulse_md,
                    "week_label": week_label,
                }
            )
            
            doc_data = json.loads(doc_result.content[0].text)
            doc_url = doc_data.get("doc_url", "")
            
            # Step 2: Create draft
            teaser = generate_teaser(pulse_md)  # Your teaser generation logic
            draft_result = await session.call_tool(
                "create_draft",
                arguments={
                    "to": recipient,
                    "subject": f"WeeklyPulse — Groww — {week_label}",
                    "body": teaser,
                    "doc_url": doc_url,
                }
            )
            
            draft_data = json.loads(draft_result.content[0].text)
            return {
                "doc": doc_data,
                "draft": draft_data,
                "status": "complete"
            }
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-29 | Initial release with create_or_update_doc and create_draft |

---

## References

- **ADR-008:** Doc as canonical source; email contains teaser + link
- **ADR-010:** Draft-only delivery; human must review and send
- **ADR-013:** Delivery order: Docs MCP before Gmail MCP
- **ADR-019:** Same-week re-run idempotency (update existing doc)
- **Phase 4 Eval:** [eval.md](../../phases/phase-04-delivery-mcp/eval.md)
