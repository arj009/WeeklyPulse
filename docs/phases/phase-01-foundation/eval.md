# Phase 1 — Foundation — Evaluation

**Phase goal:** Operating environment ready—structure, config, MCP connectivity, agent instructions, manifest template, governance.

**Reference:** [Implementation plan — Phase 1](../../phase-wise-implementation-plan.md#phase-1--foundation)

**Prerequisite:** [ProblemStatement.md](../../../ProblemStatement.md) agreed.

**Activity map:** Exit criteria below map to activities **1.1–1.6** in the implementation plan.

**Repo implementation (2026-05-30):** Activities 1.1, 1.2, 1.4, 1.5, 1.6 delivered in codebase. Activity **1.3** MCP smoke: operator runs [prompts/mcp-smoke-test.md](../../../prompts/mcp-smoke-test.md) or `scripts/phase1_smoke_google.py` and fills [smoke-mcp-notes.md](../../../data/runs/smoke-mcp-notes.md).

**Automated eval (2026-05-30):** T1, T2, T4, T5 passed via `scripts/run_phase1_eval_checks.py`.

---

## Activity checklist

| Activity | Description | Done? |
|----------|-------------|-------|
| **1.1** | Project structure and data conventions | ☑ |
| **1.2** | Configuration defaults | ☑ |
| **1.3** | MCP servers connected and smoke-tested | ☐ confirm Doc + draft in UI |
| **1.4** | Agent behavior (prompts and checklist) | ☑ |
| **1.5** | Governance and decision log seeded | ☑ |
| **1.6** | Run manifest template defined | ☑ |

---

## Exit criteria (by activity)

### Activity 1.1 — Project structure and data conventions

| # | Criterion | Pass? |
|---|-----------|-------|
| 1.1a | Directories exist: `data/raw`, `data/processed`, `data/output`, `data/runs`, `config/`, `prompts/`, `docs/` | ☑ |
| 1.1b | Weekly run naming convention documented (ISO week `YYYY-Www`) | ☑ |
| 1.1c | `.gitignore` excludes `data/raw/**`, `.env`, secrets, and large exports | ☑ |
| 1.1d | Placeholder structure documented so operator and agent know read/write paths | ☑ |

### Activity 1.2 — Configuration defaults

| # | Criterion | Pass? |
|---|-----------|-------|
| 1.2a | Config defines target app: **Groww** (iOS + Android) | ☑ |
| 1.2b | Config defines review window: **8–12 weeks** (default recorded in [decision.md](../../decision.md)) | ☑ |
| 1.2c | Config defines analysis limits: max **5** themes, top **3** in pulse, **≤250** words | ☑ |
| 1.2d | Config defines delivery: draft recipient, subject pattern, doc title pattern | ☑ |
| 1.2e | Document explains how operator changes config without editing agent prompts | ☑ |

### Activity 1.3 — MCP servers

| # | Criterion | Pass? |
|---|-----------|-------|
| 1.3a | Google **Docs** MCP configured in host | ☑ operator confirmed |
| 1.3b | **Gmail** MCP configured in host | ☑ operator confirmed |
| 1.3c | Smoke test: throwaway doc created successfully | ☐ |
| 1.3d | Smoke test: throwaway draft to self created successfully | ☐ |
| 1.3e | Tool names, required arguments, and typical responses recorded (no secrets) | ☐ |
| 1.3f | Confirmed: OAuth/credentials live in MCP config only—not in repo | ☑ |

### Activity 1.4 — Agent behavior

| # | Criterion | Pass? |
|---|-----------|-------|
| 1.4a | System prompt covers: Groww, public exports, no PII, MCP-only Google, eval gates | ☑ |
| 1.4b | Weekly run checklist: exports in folder → manifest written (ordered steps) | ☑ |
| 1.4c | Documented: agent vs deterministic steps (ingest, analyze, PII check) | ☑ |
| 1.4d | Stop conditions defined: PII fail, MCP fail, missing exports | ☑ |

### Activity 1.5 — Governance

| # | Criterion | Pass? |
|---|-----------|-------|
| 1.5a | [decision.md](../../decision.md) contains accepted ADRs for foundation decisions (see ADR index) | ☑ |
| 1.5b | Each implementation phase linked to its `eval.md` | ☑ |

### Activity 1.6 — Run manifest template

| # | Criterion | Pass? |
|---|-----------|-------|
| 1.6a | Template defines: timestamp, week id, input checksums, review counts | ☑ |
| 1.6b | Template defines: theme list, word count, PII status, MCP status | ☑ |
| 1.6c | Template defines: doc link, draft reference (no PII in manifest) | ☑ |
| 1.6d | Manifest purpose documented: operational record, not customer-facing | ☑ |

---

## Tests to run

### T1 — Repository hygiene (maps to 1.1) — **PASS** (automated)

### T2 — Config completeness (maps to 1.2) — **PASS** (automated)

### T3 — MCP smoke (maps to 1.3)

1. Docs MCP: create doc titled `WeeklyPulse-MCP-Smoke`.
2. Gmail MCP: create draft to self, subject `WeeklyPulse-MCP-Smoke`.

**Run:** [prompts/mcp-smoke-test.md](../../../prompts/mcp-smoke-test.md) in Agent, or `scripts/phase1_smoke_google.py` (browser OAuth).

### T4 — Prompt alignment (maps to 1.4) — **PASS** (automated)

### T5 — Manifest template review (maps to 1.6) — **PASS** (automated)

---

## Decisions confirmed this phase

| ADR | Topic | Accepted |
|-----|-------|----------|
| ADR-001 | Google via MCP, not repo APIs | ☑ |
| ADR-002 | Public exports only | ☑ |
| ADR-003 | Target app: Groww | ☑ |
| ADR-004 | Theme cap and pulse structure | ☑ |
| ADR-005 | PII fail-closed | ☑ |
| ADR-009 | Five-phase eval-gated build | ☑ |
| ADR-010 | Draft-only email; human sends | ☑ |
| ADR-011 | ISO week run folders | ☑ |
| ADR-012 | Default 10-week review window | ☑ |

---

## Evidence to attach

- [x] Config file in repo (`config/default.yaml`)
- [x] Manifest template (`templates/manifest.template.json`)
- [ ] Smoke-test Doc link in `smoke-mcp-notes.md`
- [ ] Gmail draft id in `smoke-mcp-notes.md`

---

## Sign-off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Implementer | Cursor agent | 2026-05-30 | ☑ (repo + automated tests) |
| Operator (MCP verified) | | | ☐ after T3 UI check |

**Phase 1 status:** ☑ In progress · ☐ **Passed** (pending T3 doc + draft confirmation)

**Notes / blockers:**

```text
MCP configured in Cursor by operator. Automated T1/T2/T4/T5 pass.
Complete T3: run prompts/mcp-smoke-test.md OR scripts/phase1_smoke_google.py (OAuth browser).
Rotate Google OAuth client secret if Credential.json was ever committed.
```
