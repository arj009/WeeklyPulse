# WeeklyPulse — Weekly run checklist

Use this checklist **in order** each ISO week (`YYYY-Www`). Aligns with [architecture sequence diagram](../docs/architecture.md#sequence-diagram).

## Entry conditions

- [ ] Fresh App Store + Play Store exports in `data/raw/`
- [ ] `config/default.yaml` valid (`python -m weeklypulse config validate`)
- [ ] Gmail `WEEKLYPULSE_DRAFT_TO` set in `.env` if required
- [ ] Google Docs + Gmail MCP servers running in Cursor
- [ ] Phase 1 eval passed; Phase 2+ only when prior phase evals pass

---

## S0 — Prepare (operator)

1. Download public Groww exports from App Store Connect / Play Console.
2. Copy files to `data/raw/` (do not commit).
3. Note filenames for manifest `inputs.files`.

---

## S1 — Ingest (pipeline — Phase 2)

4. Run: `python -m weeklypulse ingest` *(when implemented)*.
5. Confirm `data/processed/reviews.jsonl` exists.
6. Review ingestion summary: counts, date range, warnings.

**Stop if:** parse errors unrecoverable; reviews below abort threshold (ADR-017).

---

## S2 — Analyze (pipeline + agent — Phase 3)

7. Run: `python -m weeklypulse analyze` *(when implemented)*.
8. Agent: refine theme labels and action ideas for Groww context.
9. Confirm `themes.json`, `pulse.md`, `pulse.json` in `data/output/`.
10. Confirm ≤250 words (body), 3 themes / quotes / actions.

**Stop if:** cannot meet structure without violating constraints.

---

## S3 — Validate (pipeline)

11. Run PII gate on `pulse.md`.
12. **If FAIL:** scrub or pick new quotes; re-run gate. **Do not proceed to MCP.**

---

## S4 — Deliver (agent + MCP — Phase 4)

13. Re-confirm PII gate passed.
14. **Docs MCP:** create/update doc — title `WeeklyPulse — Groww — {week_label}`; body = full pulse.
15. Capture `doc_url` for manifest.
16. **Gmail MCP:** create draft — subject same pattern; body = teaser + doc link (ADR-008).
17. Capture `draft_id` for manifest.

**Stop if:** PII ambiguous; Doc failed (do not draft with broken link).

---

## S5 — Close (pipeline + operator)

18. Write `data/runs/{week_label}/manifest.json` from [template](../templates/manifest.template.json).
19. Tell operator: manifest path, doc link, draft location.
20. Operator reviews Doc and draft; edits if needed; **sends email manually**.

---

## Exit conditions

- [ ] `manifest.json` complete with `delivery_status: complete` (or `partial` with retry notes)
- [ ] No PII in any shared artifact
- [ ] Operator acknowledged handoff

---

## Quick command reference (Phases 1–5)

```bash
python -m weeklypulse config validate
python -m weeklypulse init
python -m weeklypulse ingest    # Phase 2+
python -m weeklypulse analyze   # Phase 3+
python -m weeklypulse run       # Phase 5
```
