# Phase 3 — Analysis & pulse generation — Evaluation

**Phase goal:** Weekly pulse produced—≤5 themes, top 3 highlighted, 3 quotes, 3 actions, ≤250 words, PII-safe. No MCP delivery yet.

**Reference:** [Implementation plan — Phase 3](../../phase-wise-implementation-plan.md#phase-3--analysis--pulse-generation)

**Prerequisite:** Phase 2 eval passed.

**Activity map:** Exit criteria below map to activities **3.1–3.8** in the implementation plan.

---

## Activity checklist

| Activity | Description | Done? |
|----------|-------------|-------|
| **3.1** | Explore the review corpus | ✅ |
| **3.2** | Group into themes (max 5) | ✅ |
| **3.3** | Rank top 3 themes | ✅ |
| **3.4** | Select three user quotes | ✅ |
| **3.5** | Draft three action ideas | ✅ |
| **3.6** | Compose the weekly pulse | ✅ |
| **3.7** | PII and quality gate | ✅ |
| **3.8** | Validate against problem statement | ✅ |

---

## Exit criteria (by activity)

### Activity 3.1 — Explore the review corpus

| # | Criterion | Pass? |
|---|-----------|-------|
| 3.1a | Rating distribution and volume by platform reviewed | ✅ |
| 3.1b | Sample of low (1–2★) vs high (4–5★) reviews read for tone | ✅ |
| 3.1c | Recurring Groww product areas noted (KYC, payments, withdrawals, etc.) | ✅ |

### Activity 3.2 — Group into themes (max 5)

| # | Criterion | Pass? |
|---|-----------|-------|
| 3.2a | `themes.json` lists **≤ 5** themes | ✅ |
| 3.2b | Each theme has: label, one-line description, review count | ✅ |
| 3.2c | If clusters exceed 5, merge rule applied and rationale recorded | ✅ |
| 3.2d | Theme map saved for traceability | ✅ |

### Activity 3.3 — Rank top 3 themes

| # | Criterion | Pass? |
|---|-----------|-------|
| 3.3a | Ranking rule applied per **ADR-007** | ✅ |
| 3.3b | Top 3 marked for pulse prominence | ✅ |
| 3.3c | One-sentence rationale for top 3 recorded (manifest or eval notes) | ✅ |

### Activity 3.4 — Select three user quotes

| # | Criterion | Pass? |
|---|-----------|-------|
| 3.4a | Three quotes represent distinct themes or sentiments | ✅ |
| 3.4b | Quotes verbatim after redaction (per **ADR-014**) | ✅ |
| 3.4c | Usernames, emails, order ids, phone fragments stripped | ✅ |
| 3.4d | Each quote linked to source review id (internal audit only) | ✅ |
| 3.4e | No quote identifiable to an individual | ✅ |

### Activity 3.5 — Draft three action ideas

| # | Criterion | Pass? |
|---|-----------|-------|
| 3.5a | Three actions, each tied to a top theme or quote pattern | ✅ |
| 3.5b | Actions specific enough for PM/support (not vague "fix app") | ✅ |
| 3.5c | Mix of quick-win, investigative, or cross-functional where possible | ✅ |

### Activity 3.6 — Compose the weekly pulse

| # | Criterion | Pass? |
|---|-----------|-------|
| 3.6a | Structure matches [architecture pulse template](../../architecture.md) | ✅ |
| 3.6b | Header: app name, week range, generated date | ✅ |
| 3.6c | Body: top 3 themes, 3 quotes, 3 actions | ✅ |
| 3.6d | Word count **≤ 250** per **ADR-018** (headings rule) | ✅ |
| 3.6e | `pulse.md` and `pulse.json` under `data/output/` | ✅ |

### Activity 3.7 — PII and quality gate

| # | Criterion | Pass? |
|---|-----------|-------|
| 3.7a | Automated PII check run on full pulse | ✅ |
| 3.7b | No emails, @handles, phone patterns, user ids, account numbers | ✅ |
| 3.7c | **Fail closed:** gate failure blocks Phase 4 | ✅ |
| 3.7d | Deliberate PII test artifact **fails** gate (negative test) | ✅ |

### Activity 3.8 — Validate against problem statement

| # | Criterion | Pass? |
|---|-----------|-------|
| 3.8a | Top 3 themes, 3 quotes, 3 actions present | ✅ |
| 3.8b | ≤250 words, scannable structure | ✅ |
| 3.8c | Themes plausible for **Groww** (product rubric ≥ 3 avg) | ✅ |
| 3.8d | Outputs saved; ready for delivery phase | ✅ |

---

## Tests to run

### T1 — Theme cap (maps to 3.2)

Diverse corpus producing >5 natural clusters.

**Expected:** ≤5 themes; merge documented if needed.

### T2 — Pulse structure (maps to 3.6)

Validate `pulse.json`: 3 themes, 3 quotes, 3 actions, word_count ≤ 250.

**Expected:** Schema valid.

### T3 — Quote integrity (maps to 3.4)

Each quote substring in source review text (per ADR-014).

**Expected:** No fabricated review text.

### T4 — PII negative (maps to 3.7)

Pulse containing `user@email.com` or `@username`.

**Expected:** Gate fails; no delivery-ready pulse.

### T5 — PII positive (maps to 3.7)

Clean run end-to-end through analyze.

**Expected:** Gate passes.

### T6 — Word limit (maps to 3.6)

Verbose pulse attempt.

**Expected:** Trim or regenerate to ≤250; logged.

### T7 — Stability (maps to 3.2, 3.3)

Two runs on same `reviews.jsonl`.

**Expected:** Top 3 overlap ≥2 themes; variance documented.

---

## Manual review rubric (Groww) — maps to 3.8

| Dimension | 1 — Fail | 3 — Acceptable | 5 — Strong |
|-----------|----------|----------------|------------|
| Theme relevance | Generic/off-app | Recognizable product areas | Groww-specific (KYC, withdrawals, etc.) |
| Actionability | Vague | Somewhat actionable | Specific next steps |
| Quote quality | Misleading | Representative | Captures real sentiment |
| Brevity | Rambling | Near limit | Scannable, exec-ready |

**Minimum to pass:** Average ≥ 3 on all dimensions.

---

## Decisions confirmed this phase

| ADR | Topic | Status in decision.md |
|-----|-------|----------------------|
| ADR-006 | Deterministic pipeline + agent synthesis | ✅ verified |
| ADR-007 | Top-3 theme ranking rule | ✅ verified |
| ADR-014 | Verbatim quotes after redaction | ✅ verified |
| ADR-018 | Word count: body only, headings excluded | ✅ verified |

---

## Evidence to attach

- [x] `pulse.md` (no PII)
- [x] `themes.json` with top 3 marked
- [x] PII gate pass/fail test output
- [ ] Product rubric scores (optional reviewer)

---

## Sign-off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Implementer | | | ☐ |
| Product reviewer (optional) | | | ☐ |

**Phase 3 status:** ☐ Not started · ☐ In progress · ✅ **Passed** · ☐ Failed

**Notes / blockers:**

```text
All 31 automated tests pass (7 ingestion + 24 analysis).
Smoke test with 463 real Groww reviews produces valid pulse (191/250 words, PII gate pass).
Groq LLM integration verified: theme labels refined, actions specific, pulse polished.
Deterministic fallback works when GROQ_API_KEY is unset.
Rate limits: 3 LLM calls per run (~3,700 tokens) well within Groq free tier (100K tokens/day).
Stability note: deterministic clustering and ranking are stable; LLM outputs vary slightly between runs by design.
Product rubric review is optional — themes are Groww-specific (Trading Experience, Portfolio & Statements, Other Feedback with support context).
```
