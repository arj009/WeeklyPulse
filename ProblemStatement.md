# WeeklyPulse — Problem Statement

## Context

**WeeklyPulse** is a small automation that turns recent public app-store feedback into a short, actionable weekly summary for product and growth teams. The target app for this build is **Groww** (iOS App Store and Google Play).

Reviews are imported from **public exports only** (no scraping behind logins). The pipeline clusters feedback into themes, drafts a one-page pulse, stores or formats the note in **Google Docs** via an MCP server, and sends a **draft email** to yourself via **Gmail** through an MCP server—not via direct Google REST APIs or custom OAuth clients in application code.

---

## Problem

Product, support, and leadership teams need a consistent weekly view of what users are saying in store reviews—without manually reading hundreds of posts or leaking PII into internal docs.

Turn the last **8–12 weeks** of App Store and Play Store reviews into a **one-page weekly pulse** that includes:

- Top themes (what users talk about most)
- Real user quotes (anonymized)
- Three concrete action ideas

Then deliver that pulse as a **draft email** (and optionally a linked or embedded **Google Doc**) so the recipient can skim, edit, and send.

---

## Who This Helps

| Audience | Value |
|----------|--------|
| **Product / Growth** | Prioritize fixes and experiments from recurring themes |
| **Support** | See what users praise or complain about; align responses |
| **Leadership** | Quick weekly health check on app sentiment |

---

## What You Must Build

### 1. Review ingestion

- Import reviews from the last **8–12 weeks**
- Fields: rating, title, text, date (and platform/source where available)
- **Public review exports only** — no scraping behind logins

### 2. Theme analysis

- Group reviews into **at most 5 themes** (e.g., onboarding, KYC, payments, statements, withdrawals)
- Surface the **top 3 themes** for the weekly note

### 3. Weekly one-page note

Generate a scannable note (≤ **250 words**) containing:

- **Top 3 themes** (with brief context)
- **3 user quotes** (verbatim from reviews, no usernames or identifiers)
- **3 action ideas** tied to the themes

### 4. Delivery (MCP, not APIs)

Use **MCP servers** for Google workspace integration—do **not** implement Gmail or Google Docs via direct Google APIs in the app:

| Integration | Approach |
|-------------|----------|
| **Google Docs** | MCP server — create/update or export the weekly pulse document as required by the workflow |
| **Gmail** | MCP server — compose and save/send a **draft email** to yourself (or a team alias) containing the weekly note |

Application logic should invoke these capabilities through the MCP tool interface (configured in the agent/IDE environment), keeping credentials and OAuth handled by the MCP server—not embedded API keys in the repo.

### 5. Privacy

- **Do not include PII** in any artifact (notes, docs, emails)
- No usernames, emails, device IDs, or other identifiers in quotes or summaries

---

## Key Constraints

- **Data source:** Public review exports only; no authenticated store scraping
- **Themes:** Maximum **5** themes for clustering; **3** called out in the weekly note
- **Length:** Weekly note ≤ **250 words**, scannable structure (headings/bullets)
- **Integrations:** **MCP** for Google Docs and Gmail; **not** direct Google API clients in the codebase
- **Privacy:** No PII in docs, emails, or generated text

---

## Success Criteria

- Reviews from 8–12 weeks are loaded and themed consistently week over week
- Each run produces a ≤250-word pulse with top 3 themes, 3 quotes, and 3 actions
- A draft email (via Gmail MCP) is ready for the operator to review and send
- Google Docs output (via Docs MCP), if used, matches the same content and respects PII rules
- End-to-end flow is repeatable without manual copy-paste from review files
