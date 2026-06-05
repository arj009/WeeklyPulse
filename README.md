# WeeklyPulse

Turn **Groww** App Store and Play Store public review exports into a weekly one-page pulse (top themes, quotes, action ideas) and deliver via **Google Docs + Gmail MCP**.

## Documentation

| Doc | Description |
|-----|-------------|
| [ProblemStatement.md](./ProblemStatement.md) | Requirements |
| [docs/architecture.md](./docs/architecture.md) | Context, pipeline, sequence diagrams |
| [docs/phase-wise-implementation-plan.md](./docs/phase-wise-implementation-plan.md) | Phased build plan |
| [docs/decision.md](./docs/decision.md) | Architecture decision log |
| [docs/mcp-setup.md](./docs/mcp-setup.md) | Google MCP setup and smoke tests |
| [docs/phases/README.md](./docs/phases/README.md) | Phase index and eval links |

## Project layout

```text
WeeklyPulse/
├── config/default.yaml      # Operator-tunable settings
├── data/
│   ├── raw/                 # Export drop zone (gitignored)
│   ├── processed/           # reviews.jsonl, themes.json
│   ├── output/              # pulse.md, pulse.json
│   ├── fixtures/            # Test samples (Phase 2)
│   └── runs/YYYY-Www/       # manifest.json per week
├── docs/phases/             # Per-phase eval + README
├── prompts/                 # Agent system + weekly checklist
├── src/weeklypulse/         # Pipeline by phase module
│   ├── foundation/          # Phase 1 ✓
│   ├── ingestion/           # Phase 2
│   ├── analysis/            # Phase 3
│   ├── delivery/            # Phase 4
│   └── e2e/                 # Phase 5
└── templates/manifest.template.json
```

## Quick start (Phase 1)

```bash
# Create venv and install
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e .

# Validate config and create data dirs
python -m weeklypulse config validate
python -m weeklypulse init
python -m weeklypulse --help
```

### Operator setup

1. Copy `.env.example` → `.env`; set `WEEKLYPULSE_DRAFT_TO`.
2. Configure Google Docs + Gmail MCP — [docs/mcp-setup.md](./docs/mcp-setup.md).
3. Complete smoke test — [prompts/mcp-smoke-test.md](./prompts/mcp-smoke-test.md) (MCP) or `scripts/phase1_smoke_google.py` (OAuth); fill [data/runs/smoke-mcp-notes.md](./data/runs/smoke-mcp-notes.md).
4. Sign off [Phase 1 eval](./docs/phases/phase-01-foundation/eval.md) after Doc + draft visible in Google UI.

## Operator Playbook (Phase 5 E2E)

This is your weekly guide to running the End-to-End pipeline for WeeklyPulse.

**1. Cadence**
- **When:** Every Monday morning (or a designated day).
- **Goal:** Run the agent pipeline to generate a fresh analysis of the past 10 weeks of user feedback.

**2. Before you run (Prepare)**
- **Exports:** Download fresh CSV exports for Groww from both App Store Connect and Google Play Console.
- **Placement:** Move these files directly into the `data/raw/` folder. Do not commit them to Git.
- **Config:** Check that `.env` has your `WEEKLYPULSE_DRAFT_TO` set and `GROQ_API_KEY` is loaded.

**3. Running the Pipeline (Agent Orchestration)**
You can use the CLI to execute the pipeline locally, and let the AI Agent handle delivery.
```bash
python -m weeklypulse run
```
This triggers data ingestion, processing, and Groq-powered synthesis. Wait for it to finish and prompt the next steps for delivery via MCP. (Refer to `prompts/weekly-run.md` for the explicit agent checklist).

**4. After you run (Review & Send)**
- **Verify Manifest:** The pipeline generates a `manifest.json` under `data/runs/YYYY-Www/`. Open it to verify that counts look correct and the `pii_gate` shows "pass".
- **Review Draft & Doc:** Go to your Google Drive to review the newly generated WeeklyPulse document. Go to your Gmail "Drafts" folder to find the created email.
- **Send:** Once you confirm the accuracy and format, hit **Send** on the draft to share it with stakeholders.

**5. Troubleshooting**
If the PII gate fails or a file cannot be parsed, the agent will stop. See the [Failure flow in Architecture Docs](./docs/architecture.md#4-failure-and-recovery-flow) for recovery steps.

## CLI

| Command | Phase | Description |
|---------|-------|-------------|
| `weeklypulse init` | 1 | Ensure `data/` layout |
| `weeklypulse config validate` | 1 | Validate YAML |
| `weeklypulse ingest` | 2 | Parse exports |
| `weeklypulse analyze` | 3 | Themes + pulse |
| `weeklypulse run` | 5 | Full pipeline |

## Phase 6: Cloud Automation (GitHub Actions & Railway)
WeeklyPulse supports headless execution for cloud deployments:
- **GitHub Actions (`.github/workflows/weekly_pulse.yml`)**: Runs automatically on a cron schedule. Ensure you set your Secrets (`GROQ_API_KEY`, `GOOGLE_SERVICE_ACCOUNT_JSON`, etc.).
- **Railway API (`railway.json` & `main_api.py`)**: Deploy to Railway to host a FastAPI instance. Hit the `POST /trigger` endpoint to manually trigger a run remotely.

## License

Internal / NextLeap — adjust as needed.
