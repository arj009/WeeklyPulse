# Phase 4 — Delivery (MCP) — Quick Start Guide

This guide walks you through testing and using the WeeklyPulse MCP server for Phase 4.

---

## 📋 Prerequisites

1. ✅ Python 3.10+ with virtual environment
2. ✅ `Credential.json` in project root (Google OAuth credentials)
3. ✅ Dependencies installed (see Step 1 below)

---

## 🚀 Step 1: Install Dependencies

```powershell
# Activate your virtual environment
.venv\Scripts\Activate.ps1

# Install all required packages
pip install mcp google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Or install from pyproject.toml
pip install -e .
```

---

## 🧪 Step 2: Test the MCP Server

### Option A: Test Google Docs Only

```powershell
python -m weeklypulse.delivery.mcp_google_server --test test-docs `
  --title "WeeklyPulse — Test — 2026-W22" `
  --body "# Weekly Pulse Test`n`nThis is a test of the MCP server.`n`n## Key Themes`n- Theme 1`n- Theme 2"
```

**Expected Output:**
- Browser opens for OAuth (first time only)
- Console shows: `Doc created: https://docs.google.com/document/d/...`
- Google Doc created in your Drive

### Option B: Test Gmail Draft Only

```powershell
python -m weeklypulse.delivery.mcp_google_server --test test-gmail `
  --to "your-email@gmail.com" `
  --subject "WeeklyPulse — Test — 2026-W22" `
  --body "This is a test email for the weekly pulse.`n`nView full pulse in Google Docs: https://docs.google.com/document/d/TEST"
```

**Expected Output:**
- Console shows: `Draft created: r-1234567890`
- Draft appears in Gmail Drafts folder

### Option C: Full Integration Test

```powershell
# Create a test pulse file
@"
# WeeklyPulse — Groww — 2026-W22

## Key Themes
- Theme 1: Performance improvements
- Theme 2: UI/UX enhancements

## Top User Quotes
> "The app is much faster now!" - User 123

## Action Items
- Continue performance optimization
- Address UI inconsistencies
"@ | Out-File -Encoding UTF8 data\output\test-pulse.md

# Run delivery
python -c "
from pathlib import Path
from weeklypulse.delivery.delivery import deliver_pulse_via_mcp

pulse_md = Path('data/output/test-pulse.md').read_text(encoding='utf-8')
result = deliver_pulse_via_mcp(
    pulse_md=pulse_md,
    week_label='2026-W22',
    app_name='Groww',
    recipient='your-email@gmail.com',
    manifest_path=Path('data/output/test-manifest.json'),
    dry_run=False  # Set True to skip actual MCP calls
)
print('Delivery result:', result)
"
```

---

## 🖥️ Step 3: Run as MCP Server

To run the server for use with Cursor/Qoder agents:

```powershell
python -m weeklypulse.delivery.mcp_google_server
```

**Expected Output:**
```
INFO:weeklypulse.delivery.mcp_google_server:Starting WeeklyPulse MCP Server...
INFO:weeklypulse.delivery.mcp_google_server:Press Ctrl+C to stop
```

The server will wait for MCP client connections (e.g., from Cursor).

---

## 🔐 OAuth Authentication

### First Run
1. Browser automatically opens
2. Sign in with your Google account
3. Grant permissions (Docs, Gmail, Drive)
4. `token.json` is created in project root

### Token Refresh
- Token automatically refreshes when expired
- If refresh fails, delete `token.json` and re-authenticate

### Security
- ✅ `Credential.json` and `token.json` are in `.gitignore`
- ✅ Never commit these files
- ✅ Token has minimum required scopes

---

## 📊 Step 4: Verify Delivery

### Check Google Docs
1. Open Google Drive
2. Search for: `WeeklyPulse — Groww — 2026-W22`
3. Verify content matches `pulse.md`

### Check Gmail
1. Open Gmail
2. Go to **Drafts** folder
3. Find draft with subject: `WeeklyPulse — Groww — 2026-W22`
4. Review and manually send (per ADR-010)

### Check Manifest
```powershell
Get-Content data/output/test-manifest.json | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

Expected `delivery` section:
```json
{
  "delivery": {
    "status": "complete",
    "doc_url": "https://docs.google.com/document/d/...",
    "doc_id": "1aB2cD3...",
    "doc_action": "created",
    "draft_id": "r-1234567890",
    "errors": []
  }
}
```

---

## 🔄 Step 5: Test Idempotency (ADR-019)

Run the same delivery again:

```powershell
python -m weeklypulse.delivery.mcp_google_server --test test-docs `
  --title "WeeklyPulse — Test — 2026-W22" `
  --body "# Updated Weekly Pulse`n`nThis is an updated test."
```

**Expected Output:**
- Console shows: `Doc updated: https://docs.google.com/document/d/...`
- **Same** Google Doc is updated (no duplicate created)
- Check doc's **Version history** to see both versions

---

## ❌ Troubleshooting

### Issue: "Credential.json not found"
**Solution:** Ensure `Credential.json` is in project root (`d:\NextLeap\WeeklyPulse\`)

### Issue: "OAuth token expired"
**Solution:** Delete `token.json` and run test again to re-authenticate

### Issue: "Permission denied" or "403 Forbidden"
**Solution:**
1. Open Google Cloud Console
2. Verify these APIs are enabled:
   - Google Docs API
   - Gmail API
   - Google Drive API
3. Verify OAuth consent screen is configured

### Issue: "Quota exceeded" or "429 Too Many Requests"
**Solution:** Wait a few minutes and retry. Google APIs have rate limits.

### Issue: Module not found error
**Solution:**
```powershell
# Make sure you're in the project root
cd d:\NextLeap\WeeklyPulse

# Activate venv
.venv\Scripts\Activate.ps1

# Reinstall in editable mode
pip install -e .
```

---

## 📚 Next Steps

1. **Document tool contracts:** See [mcp-tool-contracts.md](./mcp-tool-contracts.md)
2. **Run Phase 4 eval:** See [eval.md](./eval.md)
3. **Integrate with CLI:** Add delivery command to `weeklypulse.cli`
4. **Add to agent playbook:** Update Cursor agent instructions for delivery sequence

---

## 🎯 Phase 4 Checklist

- [ ] Dependencies installed
- [ ] OAuth credentials configured
- [ ] Test doc created successfully
- [ ] Test draft created successfully
- [ ] Idempotency verified (update existing doc)
- [ ] Manifest updated with delivery status
- [ ] Eval criteria met (see [eval.md](./eval.md))

---

## 📖 References

- **MCP Tool Contracts:** [mcp-tool-contracts.md](./mcp-tool-contracts.md)
- **Phase 4 Eval:** [eval.md](./eval.md)
- **MCP Setup:** [../../mcp-setup.md](../../mcp-setup.md)
- **ADR-008:** Doc canonical; email teaser + link
- **ADR-010:** Draft-only; human sends
- **ADR-013:** Docs before Gmail delivery order
- **ADR-019:** Same-week re-run idempotency
