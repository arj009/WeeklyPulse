# WeeklyPulse — Decision log

Record of **major technical and logical decisions** made while designing and building WeeklyPulse. Only decisions that are hard to reverse or affect architecture, eval criteria, or operator workflow belong here—not small implementation details.

**Format:** ADR-NNN — Title — Status (`accepted` | `superseded`)

**Related:** [architecture.md](./architecture.md) · [phase-wise-implementation-plan.md](./phase-wise-implementation-plan.md)

---

## Index

| ADR | Title | Phase | Status |
|-----|-------|-------|--------|
| [001](#adr-001--google-integrations-via-mcp-not-application-apis) | Google via MCP, not application APIs | 1 | accepted |
| [002](#adr-002--public-review-exports-only) | Public review exports only | 1 | accepted |
| [003](#adr-003--target-app-groww) | Target app: Groww | 1 | accepted |
| [004](#adr-004--theme-cap-and-pulse-structure) | Theme cap and pulse structure | 1 | accepted |
| [005](#adr-005--pii-fail-closed-before-delivery) | PII fail-closed before delivery | 1 | accepted |
| [006](#adr-006--deterministic-pipeline-agent-assisted-synthesis) | Deterministic pipeline + agent synthesis | 3 | accepted |
| [007](#adr-007--top-3-theme-ranking-rule) | Top-3 theme ranking rule | 3 | accepted |
| [008](#adr-008--doc-canonical-email-teaser--link) | Doc canonical; email teaser + link | 4 | accepted |
| [009](#adr-009--five-phase-eval-gated-implementation) | Five-phase eval-gated implementation | 1 | accepted |
| [010](#adr-010--draft-only-email-human-sends) | Draft-only email; human sends | 1, 4 | accepted |
| [011](#adr-011--iso-week-run-folders) | ISO week run folders | 1 | accepted |
| [012](#adr-012--default-10-week-review-window) | Default 10-week review window | 1, 2 | accepted |
| [013](#adr-013--docs-before-gmail-delivery-order) | Docs before Gmail delivery order | 4 | accepted |
| [014](#adr-014--verbatim-quotes-after-redaction) | Verbatim quotes after redaction | 3 | accepted |
| [015](#adr-015--include-non-english-reviews) | Include non-English reviews | 2 | superseded |
| [020](#adr-020--english-only-reviews-in-ingestion) | English-only reviews in ingestion | 2 | accepted |
| [021](#adr-021--minimum-six-words-per-review) | Minimum six words per review | 2 | accepted |
| [022](#adr-022--reject-reviews-containing-emojis) | Reject reviews containing emojis | 2 | accepted |
| [023](#adr-023--cap-ingested-reviews-at-1000) | Cap ingested reviews at 1000 | 2 | accepted |
| [024](#adr-024--optional-cli-download-public-store-apis) | Optional CLI download (public APIs) | 2 | accepted |
| [016](#adr-016--duplicate-review-handling) | Duplicate review handling | 2 | accepted |
| [017](#adr-017--minimum-in-window-review-count) | Minimum in-window review count | 2 | accepted |
| [018](#adr-018--word-count-body-only) | Word count: body only | 3 | accepted |
| [019](#adr-019--same-week-re-run-updates-doc) | Same-week re-run updates Doc | 4 | accepted |

---

## ADR-001 — Google integrations via MCP, not application APIs

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 1

**Context:** Problem statement requires Google Docs and Gmail without embedding OAuth or API clients in the repository. WeeklyPulse is built as a Cursor AI agent workflow.

**Decision:** All Google Docs and Gmail operations go through **MCP servers** configured in the agent host. The repo documents tool contracts and agent playbook steps only—no direct Google REST or SDK usage in application logic.

**Consequences:**

- Credentials and token refresh live entirely in the MCP layer.
- Tool names depend on the chosen MCP server; smoke-test per environment (Phase 1 eval 1.3).
- Local automated tests cannot hit Google without the MCP host running.

---

## ADR-002 — Public review exports only

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 1

**Context:** Avoid store-console authentication, scraping ToS risk, and fragile automation.

**Decision:** Ingest only **manually downloaded public exports** from App Store and Play Store. No automated login or authenticated scraping.

**Consequences:**

- Operator refreshes exports on a weekly cadence before each run.
- Simple compliance story; fixtures can reproduce behavior in evals.

---

## ADR-003 — Target app: Groww

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 1

**Decision:** MVP targets **Groww** on iOS and Android. Theme examples, prompts, and pulse copy assume fintech/investing context. Multi-app support is post-MVP.

---

## ADR-004 — Theme cap and pulse structure

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 1

**Decision:**

- Cluster into **maximum 5 themes** internally.
- Weekly pulse highlights **top 3 themes**, **3 user quotes**, **3 action ideas**.
- Pulse is **scannable** (headings/bullets) and **≤ 250 words** (see ADR-018 for counting rule).

**Consequences:** Phase 3 eval enforces counts and word limit before delivery.

---

## ADR-005 — PII fail-closed before delivery

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 1

**Decision:** No usernames, emails, device IDs, or account identifiers in pulse, Docs, Gmail, or committed artifacts. A **PII gate** must pass before any MCP delivery call. On failure, block delivery and return to scrub/regenerate (Phase 3 eval 3.7).

**Consequences:** May require alternate quotes if scrubbing removes too much context.

---

## ADR-006 — Deterministic pipeline, agent-assisted synthesis

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 3

**Context:** Need testable data handling and trustworthy quotes without hallucinated review text.

**Decision:**

| Concern | Owner |
|---------|--------|
| Parse exports, date filter, schema, dedupe, word count, PII detection | **Deterministic pipeline** |
| Theme labels, action wording, pulse polish | **AI agent** (structured output) |
| Google Doc and Gmail draft | **Agent via MCP** |
| Send email | **Human operator** |

**Consequences:** Quotes must trace to review ids; agent does not invent review text (see ADR-014).

---

## ADR-007 — Top-3 theme ranking rule

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 3

**Context:** Top 3 themes drive the one-page pulse; ranking must be consistent week to week.

**Decision:** **Hybrid ranking (Option C):**

1. **Primary:** Review count in the analysis window.
2. **Tie-break:** Higher share of 1–2★ reviews (severity signal).
3. **Second tie-break:** Alphabetical theme label (deterministic).

Document top-3 rationale in run manifest (one sentence).

**Consequences:** Phase 3 eval 3.3 verifies rule applied; themes with equal count resolved predictably.

---

## ADR-008 — Doc canonical; email teaser + link

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 4

**Context:** Two delivery channels; avoid duplicate editing and stale copies.

**Decision:** **Option A:**

- **Google Doc** holds the **full pulse** (canonical, editable archive).
- **Gmail draft** contains a **short teaser** (2–4 sentences: top themes summary) plus **link to the Doc**.

**Consequences:** Operator edits Doc for detail; email drives attention to the Doc. Phase 4 eval 4.1 and 4.4 verify.

---

## ADR-009 — Five-phase eval-gated implementation

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 1

**Decision:** Build in five phases (Foundation → Ingestion → Analysis → MCP Delivery → E2E), each with an `eval.md`. **Do not start phase N+1 until phase N eval passes.**

**Consequences:** Scope controlled; documentation and testing aligned to activities 1.1–5.6 in the implementation plan.

---

## ADR-010 — Draft-only email; human sends

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 1, 4

**Decision:** Gmail MCP creates a **draft only**. Operator reviews, edits, and sends manually. No auto-send in MVP.

**Consequences:** Accountability and final quality check before stakeholders receive the pulse.

---

## ADR-011 — ISO week run folders

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 1

**Decision:** Name run artifacts under `data/runs/YYYY-Www/` using **ISO week** (e.g. `2026-W22`). Subject line and doc title use the same week label.

**Consequences:** Predictable archiving; easy correlation between manifest, Doc, and email subject.

---

## ADR-012 — Default 10-week review window

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 1, 2

**Context:** Problem allows 8–12 weeks; need a single default for config and evals.

**Decision:** Default **10 weeks** lookback from run date (within allowed 8–12 range). Config may override to 8 or 12.

**Consequences:** Phase 2 window filter and ingestion summary use this default unless config says otherwise.

---

## ADR-013 — Docs before Gmail delivery order

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 4

**Decision:** Agent delivery sequence is always:

1. PII gate re-check  
2. **Google Docs MCP** (create/update) → capture URL  
3. **Gmail MCP** (draft with teaser + doc link)  
4. Manifest  

Never create a Gmail draft with a doc link before the Doc exists.

**Consequences:** Avoids broken links in email; partial failure leaves Doc even if draft fails.

---

## ADR-014 — Verbatim quotes after redaction

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 3

**Decision:** User quotes in the pulse are **verbatim** from review text after PII redaction—not paraphrased or model-generated. Each quote links to a source `review id` internally for audit.

**Consequences:** Phase 3 eval T3 verifies substring match in source. If a quote cannot be used safely, select a different review.

---

## ADR-015 — Include non-English reviews

**Status:** superseded by [ADR-020](#adr-020--english-only-reviews-in-ingestion)  
**Date:** 2026-05-29  
**Phase:** 2

**Decision (original):** Include non-English reviews. **Superseded** — operator requires English-only corpus for pulse generation.

---

## ADR-020 — English-only reviews in ingestion

**Status:** accepted  
**Date:** 2026-05-30  
**Phase:** 2

**Decision:** During ingestion normalization, **drop non-English** reviews using `langdetect` with configurable minimum confidence (default **0.7**). Count drops in `excluded_by_filters.not_english`.

**Consequences:** Pulse quotes and themes reflect English feedback only; Hindi/regional reviews excluded.

---

## ADR-021 — Minimum six words per review

**Status:** accepted  
**Date:** 2026-05-30  
**Phase:** 2

**Decision:** Keep reviews only when **combined title + body** has at least **6 words**. Shorter rows are excluded (`too_few_words`).

**Consequences:** Star-only or one-line noise removed before analysis.

---

## ADR-022 — Reject reviews containing emojis

**Status:** accepted  
**Date:** 2026-05-30  
**Phase:** 2

**Decision:** **Reject** any review whose combined title + body contains emoji characters (not strip). Count as `contains_emoji` in ingestion summary.

**Consequences:** Pulse text stays plain and professional; no emoji in downstream artifacts.

---

## ADR-023 — Cap ingested reviews at 1000

**Status:** accepted  
**Date:** 2026-05-30  
**Phase:** 2

**Decision:** After filters and dedupe, keep at most **1000** reviews, preferring **newest** `review_date`. Config key `ingestion.max_reviews` (`0` = no cap). Excess count recorded as `capped_to_max_reviews` in ingestion summary.

**Consequences:** Large exports do not overload analysis; operator still downloads full export to `data/raw/` but pipeline trims for processing.

---

## ADR-024 — Optional CLI download (public store APIs)

**Status:** accepted  
**Date:** 2026-05-30  
**Phase:** 2

**Context:** Operators may not have immediate access to console CSV export; MVP needs real Groww volume.

**Decision:** Provide `weeklypulse download` using **public** Play Store (google-play-scraper) and App Store (iTunes RSS) APIs. Writes CSV to `data/raw/` in parser-compatible format, then `ingest` as usual. Manual console export remains preferred for production (ADR-002).

**Consequences:** iOS RSS is capped (~500 per run); Play can reach 1000. Downloaded rows still pass normalization filters.

---

## ADR-016 — Duplicate review handling

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 2

**Decision:** When the same review appears on re-ingest or across files, dedupe by stable `id`. **Keep the record with the latest `review_date`** if metadata differs; log dedupe count in ingestion summary.

**Consequences:** Re-running ingest on overlapping exports does not inflate theme counts.

---

## ADR-017 — Minimum in-window review count

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 2

**Decision:** Warn in ingestion summary if in-window reviews **< 30**. **Abort analysis** if **< 10** (insufficient signal)—manifest notes reason. Thresholds configurable later.

**Consequences:** Phase 2 eval T6 uses these gates; operator may wait for more export data.

---

## ADR-018 — Word count: body only

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 3

**Decision:** **250-word limit applies to pulse body** (themes, quotes, actions). Header lines (app name, week range, generated date) and section headings **do not** count toward the limit.

**Consequences:** Phase 3 eval 3.6d; automated check documented in pulse.json `word_count` field definition.

---

## ADR-019 — Same-week re-run updates Doc

**Status:** accepted  
**Date:** 2026-05-29  
**Phase:** 4

**Decision:** Re-running WeeklyPulse for the **same ISO week** **updates the existing Google Doc** for that week (same title) rather than creating a new Doc. Gmail creates a **new draft**; operator deletes stale drafts manually.

**Consequences:** Phase 4 eval 4.6 and Phase 5 eval 5.3c; manifest records `updated_at` on re-run.

---

## Superseded / rejected (for reference)

| Idea | Outcome | Reason |
|------|---------|--------|
| Direct Google APIs in repo | **Rejected** | ADR-001; MCP-only |
| Auto-send email without review | **Rejected** | ADR-010; human in loop |
| Email body as full pulse (Option B) | **Rejected** | ADR-008; Doc canonical |
| Filter non-English reviews | **Accepted** | ADR-020; English only (supersedes ADR-015) |
| Include reviews under 6 words | **Rejected** | ADR-021 |
| Allow emojis in reviews | **Rejected** | ADR-022 |
| New Doc on every same-week re-run | **Rejected** | ADR-019; update in place |

---

## ADR-025 — Headless Orchestration for Cloud

**Status:** accepted
**Date:** 2026-06-05
**Phase:** 6

**Context:** GitHub Actions and Railway do not have access to Cursor's MCP layer.
**Decision:** Replace the Cursor AI agent orchestration with a deterministic Python orchestrator that natively uses the Google APIs (via Service Accounts) while running in the cloud.
**Consequences:** MCP is only used for local dev/MVP; production uses direct APIs.

---

## ADR-026 — GitHub Actions & Railway Dual Deployment

**Status:** accepted
**Date:** 2026-06-05
**Phase:** 6

**Context:** Need both scheduled runs and on-demand triggers.
**Decision:** Use GitHub Actions for the scheduled cron job, and Railway to host a lightweight FastAPI server for on-demand HTTP triggers and dashboard integrations.
**Consequences:** Maintain `.github/workflows` and `railway.json` in the repo.
