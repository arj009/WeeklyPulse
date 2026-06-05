#!/usr/bin/env python3
"""
Operator smoke test: create Google Doc + Gmail draft (Phase 1 eval T3).

NOT part of the weeklypulse package (ADR-001). Use to verify Google OAuth
while MCP tool names are recorded separately in data/runs/smoke-mcp-notes.md.

Requires: Credential.json (OAuth client) and first-run browser consent → token.json
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CREDENTIALS = REPO_ROOT / "Credential.json"
TOKEN_PATH = REPO_ROOT / "token.json"
ENV_PATH = REPO_ROOT / ".env"

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.compose",
]

DOC_TITLE = "WeeklyPulse-MCP-Smoke"
EMAIL_SUBJECT = "WeeklyPulse-MCP-Smoke"
EMAIL_BODY = (
    "WeeklyPulse MCP smoke test.\n\n"
    "If you see this draft, Gmail compose scope works.\n"
    "Production delivery uses MCP tools in Cursor (ADR-001).\n"
)


def _load_draft_to() -> str:
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line.startswith("WEEKLYPULSE_DRAFT_TO=") and not line.endswith("="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("WEEKLYPULSE_DRAFT_TO", "").strip()


def _credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN_PATH.is_file():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS.is_file():
                raise FileNotFoundError(f"Missing {CREDENTIALS}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    return creds


def create_smoke_doc(creds) -> tuple[str, str]:
    from googleapiclient.discovery import build

    docs = build("docs", "v1", credentials=creds)
    doc = docs.documents().create(body={"title": DOC_TITLE}).execute()
    doc_id = doc["documentId"]
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": "WeeklyPulse smoke test document.\n",
                    }
                }
            ]
        },
    ).execute()
    url = f"https://docs.google.com/document/d/{doc_id}/edit"
    return doc_id, url


def create_smoke_draft(creds, to: str, doc_url: str) -> str:
    import base64
    from email.mime.text import MIMEText

    from googleapiclient.discovery import build

    body = EMAIL_BODY + f"\nDoc link: {doc_url}\n"
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = EMAIL_SUBJECT
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    gmail = build("gmail", "v1", credentials=creds)
    draft = (
        gmail.users()
        .drafts()
        .create(userId="me", body={"message": {"raw": raw}})
        .execute()
    )
    return draft["id"]


def main() -> int:
    to = _load_draft_to()
    if not to:
        print("Set WEEKLYPULSE_DRAFT_TO in .env", file=sys.stderr)
        return 1

    print("Authenticating (browser may open on first run)...")
    creds = _credentials()

    print(f"Creating Doc: {DOC_TITLE}")
    doc_id, doc_url = create_smoke_doc(creds)
    print(f"  doc_id={doc_id}")
    print(f"  url={doc_url}")

    print(f"Creating Gmail draft to {to}")
    draft_id = create_smoke_draft(creds, to, doc_url)
    print(f"  draft_id={draft_id}")

    print("\n--- Record in data/runs/smoke-mcp-notes.md ---")
    print(f"doc_url={doc_url}")
    print(f"draft_id={draft_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
