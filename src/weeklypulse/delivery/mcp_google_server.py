"""WeeklyPulse MCP Server — Google Docs and Gmail integration.

This is a complete MCP (Model Context Protocol) server that exposes
Google Docs and Gmail tools for the WeeklyPulse agent.

Usage:
    python -m weeklypulse.delivery.mcp_google_server

The server will start and wait for MCP client connections.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# MCP SDK imports
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

# ── Configuration ─────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/drive.readonly",  # For finding existing docs
]

CREDENTIAL_FILE = "Credential.json"
TOKEN_FILE = "token.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── OAuth Helpers ─────────────────────────────────────────────────────────


def get_credential_path() -> Path:
    """Find Credential.json in project root or current directory."""
    candidates = [
        Path(__file__).resolve().parents[3] / CREDENTIAL_FILE,  # project root
        Path.cwd() / CREDENTIAL_FILE,
        Path.home() / ".config" / "weeklypulse" / CREDENTIAL_FILE,
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        f"{CREDENTIAL_FILE} not found. Download from Google Cloud Console "
        "→ APIs & Services → Credentials → OAuth 2.0 Client IDs"
    )


def get_token_path() -> Path:
    """Get path to token.json (created after first OAuth)."""
    return Path(__file__).resolve().parents[3] / TOKEN_FILE


def get_credentials() -> Credentials:
    """Load or refresh Google OAuth credentials."""
    token_path = get_token_path()
    creds = None
    
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
            logger.info("Credentials refreshed")
        else:
            credential_path = get_credential_path()
            logger.info(f"Starting OAuth flow using {credential_path}")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credential_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
            token_path.write_text(creds.to_json())
            logger.info("New credentials obtained and saved")
    
    return creds


# ── Google Docs Implementation ────────────────────────────────────────────


def _impl_create_or_update_doc(title: str, body: str, week_label: str = "") -> dict[str, Any]:
    """Create or update a Google Doc with the weekly pulse content.
    
    Idempotent: if a doc with the same title exists, it updates the content
    rather than creating a duplicate (per ADR-019).
    
    Args:
        title: Document title (e.g., "WeeklyPulse — Groww — 2026-W22")
        body: Pulse content in markdown format
        week_label: ISO week label for idempotency (e.g., "2026-W22")
        
    Returns:
        Dict with doc_id, doc_url, and action (created/updated)
    """
    try:
        creds = get_credentials()
        docs_service = build("docs", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)
        
        # Check for existing doc (idempotency per ADR-019)
        query = f"name='{title}' and trashed=false"
        results = drive_service.files().list(
            q=query, 
            fields="files(id, name, modifiedTime)",
            orderBy="modifiedTime desc"
        ).execute()
        files = results.get("files", [])
        
        if files:
            # Update existing doc
            doc_id = files[0]["id"]
            logger.info(f"Updating existing doc: {doc_id}")
            _update_doc_content(docs_service, doc_id, body)
            action = "updated"
        else:
            # Create new doc
            logger.info(f"Creating new doc: {title}")
            document = docs_service.documents().create(
                body={"title": title}
            ).execute()
            doc_id = document.get("documentId")
            
            # Add content
            _update_doc_content(docs_service, doc_id, body)
            action = "created"
        
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        
        return {
            "doc_id": doc_id,
            "doc_url": doc_url,
            "action": action,
            "title": title,
        }
        
    except HttpError as error:
        logger.error(f"Google Docs API error: {error}")
        raise RuntimeError(f"Failed to create/update doc: {error}") from error
    except Exception as error:
        logger.error(f"Unexpected error: {error}")
        raise


def _update_doc_content(docs_service, doc_id: str, body: str):
    """Replace doc content with new markdown text."""
    content = _markdown_to_docs_text(body)
    
    # Get document structure
    document = docs_service.documents().get(documentId=doc_id).execute()
    body_content = document.get("body", {}).get("content", [])
    
    # Build requests - only delete if document has meaningful content
    requests = []
    
    # Check if document has actual content (more than just empty paragraph)
    if len(body_content) > 1:
        # Find the end index of the last element
        last_element = body_content[-1]
        end_index = last_element.get("endIndex", 1)
        
        # Only add delete request if there's content to delete
        # Subtract 1 to avoid including the final newline character
        if end_index > 2:
            requests.append({
                "deleteContentRange": {
                    "range": {
                        "startIndex": 1,
                        "endIndex": end_index - 1,  # Exclude final newline
                    }
                }
            })
    
    # Insert new content at the beginning
    requests.append({
        "insertText": {
            "location": {"index": 1},
            "text": content,
        }
    })
    
    # Execute batch update
    if requests:
        docs_service.documents().batchUpdate(
            documentId=doc_id, 
            body={"requests": requests}
        ).execute()


def _markdown_to_docs_text(markdown: str) -> str:
    """Convert markdown to text suitable for Google Docs.
    
    For MVP, we use plain text with basic structure.
    Future enhancement: use rich text formatting requests.
    """
    lines = markdown.split("\n")
    cleaned = []
    for line in lines:
        # Remove heading markers but keep text
        if line.startswith("# "):
            line = line[2:]
        elif line.startswith("## "):
            line = line[3:]
        elif line.startswith("### "):
            line = line[4:]
        
        # Remove bold/italic markers
        line = line.replace("**", "").replace("*", "")
        
        cleaned.append(line)
    
    return "\n".join(cleaned)


# ── Gmail Implementation ──────────────────────────────────────────────────


def _impl_create_draft(
    to: str,
    subject: str,
    body: str,
    doc_url: str = "",
) -> dict[str, Any]:
    """Create a Gmail draft for the weekly pulse email.
    
    Draft-only per ADR-010; human must review and send.
    
    Args:
        to: Recipient email address
        subject: Email subject (e.g., "WeeklyPulse — Groww — 2026-W22")
        body: Email body text (teaser + doc link per ADR-008)
        doc_url: Link to Google Doc (optional)
        
    Returns:
        Dict with draft_id
    """
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)
        
        # Compose email
        message = _create_message(to, subject, body, doc_url)
        
        # Create draft
        draft = (
            service.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": message}})
            .execute()
        )
        
        draft_id = draft["id"]
        logger.info(f"Draft created: {draft_id}")
        
        return {
            "draft_id": draft_id,
            "to": to,
            "subject": subject,
        }
        
    except HttpError as error:
        logger.error(f"Gmail API error: {error}")
        raise RuntimeError(f"Failed to create draft: {error}") from error
    except Exception as error:
        logger.error(f"Unexpected error: {error}")
        raise


def _create_message(to: str, subject: str, body: str, doc_url: str = "") -> str:
    """Create a MIME message encoded in base64.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body (teaser with key sections)
        doc_url: Google Doc URL (appended at end)
    """
    import base64
    from email.mime.text import MIMEText
    
    # Build complete email body
    text_body = body
    if doc_url:
        text_body += f"\n\n{doc_url}"
    
    message = MIMEText(text_body, "plain", "utf-8")
    message["to"] = to
    message["subject"] = subject
    
    # Encode
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return raw


# ── MCP Server Definition ─────────────────────────────────────────────────


app = FastMCP("WeeklyPulse Google Services")


@app.tool()
async def create_or_update_doc(
    title: str,
    body: str,
    week_label: str = "",
) -> TextContent:
    """Create or update a Google Doc with the weekly pulse content.
    
    Idempotent: updates existing doc for the same week title.
    
    Args:
        title: Document title (e.g., "WeeklyPulse — Groww — 2026-W22")
        body: Pulse content in markdown format
        week_label: ISO week label for idempotency (e.g., "2026-W22")
    """
    try:
        result = _impl_create_or_update_doc(title=title, body=body, week_label=week_label)
        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
        )
    except Exception as e:
        return TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2),
        )


@app.tool()
async def create_draft(
    to: str,
    subject: str,
    body: str,
    doc_url: str = "",
) -> TextContent:
    """Create a Gmail draft for the weekly pulse email.
    
    Draft-only; human must review and send.
    
    Args:
        to: Recipient email address
        subject: Email subject (e.g., "WeeklyPulse — Groww — 2026-W22")
        body: Email body text (teaser + doc link)
        doc_url: Link to Google Doc (optional)
    """
    try:
        result = _impl_create_draft(to=to, subject=subject, body=body, doc_url=doc_url)
        return TextContent(
            type="text",
            text=json.dumps(result, indent=2),
        )
    except Exception as e:
        return TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2),
        )


# ── Entry Point ───────────────────────────────────────────────────────────


def main():
    """Run the MCP server."""
    import sys
    
    if "--test" in sys.argv:
        # Test mode: run tools directly
        _test_mode(sys.argv)
    else:
        # Normal mode: start MCP server
        logger.info("Starting WeeklyPulse MCP Server...")
        logger.info("Press Ctrl+C to stop")
        app.run()


def _test_mode(argv: list[str]):
    """Test the MCP tools directly without running the server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MCP tools")
    parser.add_argument("command", choices=["test-docs", "test-gmail"])
    parser.add_argument("--title", help="Doc title for test")
    parser.add_argument("--body", help="Content for test")
    parser.add_argument("--to", help="Recipient email for test")
    parser.add_argument("--subject", help="Email subject for test")
    
    args = parser.parse_args(argv[2:])
    
    if args.command == "test-docs":
        if not args.title or not args.body:
            parser.error("--title and --body required for test-docs")
        
        result = _impl_create_or_update_doc(
            title=args.title,
            body=args.body,
            week_label="test",
        )
        print(f"Doc {result['action']}: {result['doc_url']}")
        
    elif args.command == "test-gmail":
        if not args.to or not args.subject or not args.body:
            parser.error("--to, --subject, and --body required for test-gmail")
        
        result = _impl_create_draft(
            to=args.to,
            subject=args.subject,
            body=args.body,
        )
        print(f"Draft created: {result['draft_id']}")


if __name__ == "__main__":
    main()
