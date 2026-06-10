"""WeeklyPulse CLI — phase stubs through Phase 5."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from weeklypulse import __version__
from weeklypulse.config import ConfigError, load_config


def _cmd_config_validate(_: argparse.Namespace) -> int:
    try:
        cfg = load_config()
        app = cfg["app"]["name"]
        weeks = cfg["ingestion"]["review_window_weeks"]
        print(f"Config OK — app={app}, review_window_weeks={weeks}")
        return 0
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        return 1


def _cmd_download(args: argparse.Namespace) -> int:
    from weeklypulse.ingestion import run_download

    try:
        cfg = load_config()
        count = int(args.count) if args.count else None
        result = run_download(cfg, count=count)
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        return 1

    play = result["play_store"]
    ios = result["app_store"]
    print(f"Download OK - Play: {play['downloaded']} rows -> {play['path']}")
    print(f"             iOS:  {ios['downloaded']} rows -> {ios['path']}")
    print("Next: python -m weeklypulse ingest")
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    from weeklypulse.ingestion import run_ingestion

    try:
        cfg = load_config()
        input_dir = Path(args.input).resolve() if args.input else None
        summary = run_ingestion(cfg, input_dir=input_dir, as_of=args.as_of)
    except Exception as e:
        print(f"Ingest failed: {e}", file=sys.stderr)
        return 1

    count = summary["reviews_in_window_count"]
    print(f"Ingest OK - {count} reviews -> {summary['output']}")
    print(f"  Platform: {summary['by_platform']}")
    print(f"  Excluded (window): {summary['excluded_by_window']}")
    print(f"  Excluded (filters): {summary['excluded_by_filters']}")
    if summary.get("warnings"):
        for w in summary["warnings"]:
            print(f"  Warning: {w}")
    if summary.get("abort_recommended"):
        print("  Abort recommended: below min_reviews_abort threshold", file=sys.stderr)
        return 2
    return 0


def _cmd_analyze(args: argparse.Namespace) -> int:
    from weeklypulse.analysis import run_analysis

    try:
        cfg = load_config()
        summary = run_analysis(cfg, as_of=args.as_of)
    except Exception as e:
        print(f"Analyze failed: {e}", file=sys.stderr)
        return 1

    print(f"Analyze OK - {summary['review_count']} reviews, {summary['theme_count']} themes")
    print(f"  Top 3: {', '.join(summary['top_3'])}")
    print(f"  Quotes: {summary['quotes_selected']}")
    print(f"  Word count: {summary['body_word_count']}/{summary['word_limit']}")
    print(f"  PII gate: {summary['pii_gate']}")
    print(f"  Themes: {summary['themes_json']}")
    print(f"  Pulse: {summary['pulse_md']}")

    if summary["status"] == "pii_failed":
        print(f"  WARNING: {summary['message']}", file=sys.stderr)
        return 2

    if not summary["within_word_limit"]:
        print("  WARNING: Pulse exceeds word limit", file=sys.stderr)

    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    from weeklypulse.ingestion import run_download, run_ingestion
    from weeklypulse.analysis import run_analysis
    from weeklypulse.delivery.delivery import deliver_pulse_via_mcp
    from weeklypulse.config import load_config
    from pathlib import Path
    import os
    
    try:
        cfg = load_config()
        print("Starting E2E run pipeline...")
        
        # 0. Download latest reviews
        print("\n--- Step 0: Downloading Reviews ---")
        print("Downloading from Play Store and App Store...")
        download_result = run_download(cfg, count=None)
        print(f"✅ Play Store reviews downloaded to: {download_result['play_store']['path']}")
        print(f"✅ App Store reviews downloaded to: {download_result['app_store']['path']}")
        
        # 1. Ingest
        print("\n--- Step 1: Ingesting ---")
        summary_ingest = run_ingestion(cfg, as_of=args.as_of if hasattr(args, 'as_of') else None)
        if summary_ingest.get("abort_recommended"):
            print("Abort recommended during ingestion.", file=sys.stderr)
            return 2
        
        # 2. Analyze
        print("\n--- Step 2: Analyzing ---")
        summary_analyze = run_analysis(cfg, as_of=args.as_of if hasattr(args, 'as_of') else None)
        if summary_analyze["status"] == "pii_failed":
            print(f"PII Gate Failed: {summary_analyze['message']}", file=sys.stderr)
            return 2
        
        # 3. Deliver via MCP (Google Docs + Gmail)
        print("\n--- Step 3: Delivering via MCP ---")
        week_label = summary_analyze.get("week_label", "unknown")
        pulse_md = summary_analyze.get("pulse_md", "")
        app_name = cfg.get("app_name", "Groww")
        recipient = os.environ.get("WEEKLYPULSE_DRAFT_TO", "aunkarranjan@gmail.com")
        manifest_path = Path(cfg.get("manifest_path", "data/manifest.json"))
        
        if not pulse_md:
            print("ERROR: No pulse content to deliver", file=sys.stderr)
            return 2
        
        print(f"Delivering pulse for {week_label}...")
        print(f"App: {app_name}")
        print(f"Recipient: {recipient}")
        
        delivery_result = deliver_pulse_via_mcp(
            pulse_md=pulse_md,
            week_label=week_label,
            app_name=app_name,
            recipient=recipient,
            manifest_path=manifest_path,
            dry_run=False,
        )
        
        if delivery_result["delivery_status"] == "complete":
            print(f"\n✅ Delivery complete!")
            print(f"   Doc URL: {delivery_result.get('doc_url')}")
            print(f"   Draft ID: {delivery_result.get('draft_id')}")
            print(f"\n📧 Check Gmail Drafts and send the email!")
        else:
            print(f"\n⚠️ Delivery status: {delivery_result['delivery_status']}")
            if delivery_result.get("errors"):
                print(f"   Errors: {delivery_result['errors']}", file=sys.stderr)
            return 2
            
        print("\n--- Pipeline Complete ---")
        return 0
        
    except Exception as e:
        print(f"Run failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def _cmd_init_layout(_: argparse.Namespace) -> int:
    """Ensure data directories exist (Phase 1)."""
    from weeklypulse.foundation.layout import ensure_data_layout

    ensure_data_layout()
    print("Data layout ready under data/")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weeklypulse",
        description="WeeklyPulse — Groww app store review weekly pulse",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create data directory layout")
    p_init.set_defaults(handler=_cmd_init_layout)

    p_cfg = sub.add_parser("config", help="Configuration commands")
    cfg_sub = p_cfg.add_subparsers(dest="config_cmd", required=True)
    p_validate = cfg_sub.add_parser("validate", help="Validate default.yaml")
    p_validate.set_defaults(handler=_cmd_config_validate)

    p_dl = sub.add_parser("download", help="Download public store reviews to data/raw (Phase 2)")
    p_dl.add_argument(
        "--count",
        "-n",
        type=int,
        help="Reviews per platform (default: config download.count_per_platform)",
    )
    p_dl.set_defaults(handler=_cmd_download)

    p_ingest = sub.add_parser("ingest", help="Ingest store exports (Phase 2)")
    p_ingest.add_argument(
        "--input",
        "-i",
        help="Directory with CSV exports (default: config ingestion.raw_input_dir)",
    )
    p_ingest.add_argument(
        "--as-of",
        help="Window end date YYYY-MM-DD (default: today)",
    )
    p_ingest.set_defaults(handler=_cmd_ingest)

    p_analyze = sub.add_parser("analyze", help="Analyze reviews and build pulse (Phase 3)")
    p_analyze.add_argument(
        "--as-of",
        help="Run date YYYY-MM-DD (default: today)",
    )
    p_analyze.set_defaults(handler=_cmd_analyze)

    p_run = sub.add_parser("run", help="Full weekly pipeline (Phase 5)")
    p_run.set_defaults(handler=_cmd_run)

    return parser


def main(argv: list[str] | None = None) -> None:
    # Load .env before anything else so GROQ_API_KEY etc. are available
    from dotenv import load_dotenv
    load_dotenv()

    parser = build_parser()
    args = parser.parse_args(argv)
    code = args.handler(args)
    sys.exit(code)


if __name__ == "__main__":
    main()
