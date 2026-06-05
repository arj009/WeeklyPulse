"""Phase 2 — Ingestion: parse, filter, normalize store exports."""

from weeklypulse.ingestion.download import run_download
from weeklypulse.ingestion.pipeline import run_ingestion

__all__ = ["run_download", "run_ingestion"]
