#!/usr/bin/env python3
"""Run automated Phase 1 eval checks (T1, T2, T4, T5)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def check_t2_config() -> bool:
    r = subprocess.run(
        [sys.executable, "-m", "weeklypulse", "config", "validate"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    ok = r.returncode == 0
    print(f"T2 config validate: {'PASS' if ok else 'FAIL'} — {r.stdout.strip() or r.stderr.strip()}")
    return ok


def check_t4_prompts() -> bool:
    required = ["Groww", "PII", "MCP", "250", "5 themes", "public export"]
    prompts_dir = REPO_ROOT / "prompts"
    text = ""
    for p in prompts_dir.glob("*.md"):
        text += p.read_text(encoding="utf-8").lower()
    missing = [k for k in required if k.lower() not in text]
    ok = not missing
    print(f"T4 prompt alignment: {'PASS' if ok else 'FAIL'}" + (f" missing {missing}" if missing else ""))
    return ok


def check_t5_manifest() -> bool:
    template = REPO_ROOT / "templates" / "manifest.template.json"
    example = REPO_ROOT / "data" / "runs" / "example" / "manifest.example.json"
    if not template.is_file() or not example.is_file():
        print("T5 manifest template: FAIL — files missing")
        return False
    t = json.loads(template.read_text(encoding="utf-8"))
    required_keys = ["week_label", "inputs", "analysis", "pii_gate", "delivery"]
    ok = all(k in t for k in required_keys)
    print(f"T5 manifest template: {'PASS' if ok else 'FAIL'}")
    return ok


def check_t1_gitignore() -> bool:
    gi = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    ok = "data/raw" in gi and ".env" in gi
    print(f"T1 gitignore rules: {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> int:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    results = [
        check_t1_gitignore(),
        check_t2_config(),
        check_t4_prompts(),
        check_t5_manifest(),
    ]
    passed = sum(results)
    print(f"\nAutomated checks: {passed}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
