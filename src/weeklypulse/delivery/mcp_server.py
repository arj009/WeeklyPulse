"""WeeklyPulse MCP Server — Google Docs and Gmail integration.

This server implements the Model Context Protocol (MCP) to expose
Google Docs and Gmail tools for the WeeklyPulse agent.

Tools:
- create_or_update_doc: Create/update a Google Doc with the weekly pulse
- create_draft: Create a Gmail draft for the weekly pulse email

Credentials:
- OAuth credentials stored in Credential.json (gitignored)
- Token stored in token.json (gitignored)
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

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/gmail.compose",
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── OAuth Helpers ─────────────────────────────────────────────────────────


def get_credentials() -> Credentials:
    """Load or refresh Google OAuth credentials."""
    creds_path = Path(__file__).parent / "token.json"
    credential_path = Path(__file__).parent / "Credential.json"
    
    creds = None
    if creds_path.exists():
        creds = Credentials.from_authorized_user_file(str(creds_path), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            creds_path.write_text(creds.to_json())
            logger.info("Credentials refreshed")
        else:
            if not credential_path.exists():
                raise FileNotFoundError(
                    f"Credential.json not found at {credential_path}. "
                    "Download from Google Cloud Console → APIs & Services → Credentials"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credential_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
            creds_path.write_text(creds.to_json())
            logger.info("New credentials obtained")
    
    return creds


# ── Google Docs Tools ─────────────────────────────────────────────────────


def create_or_update_doc(title: str, body: str, week_label: str = "") -> dict[str, str]:
    """Create or update a Google Doc with the weekly pulse content.
    
    Args:
        title: Document title (e.g., "WeeklyPulse — Groww — 2026-W22")
        body: Pulse content in markdown format
        week_label: ISO week label for idempotency (e.g., "2026-W22")
        
    Returns:
        Dict with doc_id, doc_url, and action (created/updated)
    """
    try:
        creds = get_credentials()
        service = build("docs", "v1", credentials=creds)
        
        # Try to find existing doc for this week (idempotency)
        drive_service = build("drive", "v3", credentials=creds)
        query = f"name='{title}' and trashed=false"
        results = drive_service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])
        
        if files:
            # Update existing doc
            doc_id = files[0]["id"]
            logger.info(f"Updating existing doc: {doc_id}")
            _update_doc_content(service, doc_id, body)
            action = "updated"
        else:
            # Create new doc
            logger.info(f"Creating new doc: {title}")
            document = service.documents().create(body={"title": title}).execute()
            doc_id = document.get("documentId")
            
            # Add content
            _update_doc_content(service, doc_id, body)
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


def _update_doc_content(service, doc_id: str, body: str):
    """Replace doc content with new markdown text."""
    # Convert markdown to simple text for Docs API
    # For MVP, we use plain text with basic formatting
    content = _markdown_to_docs_text(body)
    
    # Clear existing content
    requests = [
        {
            "deleteContentRange": {
                "range": {
                    "startIndex": 0,
                    "endIndex": 1,
                }
            }
        }
    ]
    
    # Insert new content
    requests.append(
        {
            "insertText": {
                "location": {"index": 1},
                "text": content,
            }
        }
    )
    
    service.documents().batchUpdate(
        documentId=doc_id, body={"requests": requests}
    ).execute()


def _markdown_to_docs_text(markdown: str) -> str:
    """Convert markdown to plain text suitable for Google Docs.
    
    For MVP, we keep it simple. Future enhancement: use rich text requests.
    """
    # Remove markdown formatting, keep structure
    lines = markdown.split("\n")
    cleaned = []
    for line in lines:
        # Remove heading markers but keep text
        if line.startswith("# "):
            line = line[2:].upper()
        elif line.startswith("## "):
            line = line[3:].upper()
        elif line.startswith("### "):
            line = line[4:].upper()
        
        # Remove bold/italic markers
        line = line.replace("**", "").replace("*", "")
        
        cleaned.append(line)
    
    return "\n".join(cleaned)


# ── Gmail Tools ───────────────────────────────────────────────────────────


def create_draft(
    to: str,
    subject: str,
    body: str,
    doc_url: str = "",
    html: bool = False,
) -> dict[str, str]:
    """Create a Gmail draft for the weekly pulse email.
    
    Args:
        to: Recipient email address
        subject: Email subject (e.g., "WeeklyPulse — Groww — 2026-W22")
        body: Email body text
        doc_url: Link to Google Doc (optional)
        html: Whether body is HTML (default: False)
        
    Returns:
        Dict with draft_id
    """
    try:
        creds = get_credentials()
        service = build("gmail", "v1", credentials=creds)
        
        # Compose email
        message = _create_message(to, subject, body, doc_url, html)
        
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


def _create_message(
    to: str, subject: str, body: str, doc_url: str = "", html: bool = False
) -> str:
    """Create a MIME message encoded in base64."""
    import base64
    from email.mime.text import MIMEText
    
    if html and doc_url:
        # HTML with doc link
        html_body = f"""
        <html>
        <body>
        {body}
        <br><br>
        <p><a href="{doc_url}">View full pulse in Google Docs</a></p>
        </body>
        </html>
        """
        message = MIMEText(html_body, "html", "utf-8")
    else:
        # Plain text with doc link
        text_body = body
        if doc_url:
            text_body += f"\n\nView full pulse: {doc_url}"
        message = MIMEText(text_body, "plain", "utf-8")
    
    message["to"] = to
    message["subject"] = subject
    
    # Encode
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return raw


# ── MCP Server Interface ──────────────────────────────────────────────────


def handle_tool_call(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Route MCP tool calls to the appropriate function.
    
    This is the main entry point for the agent to call tools.
    
    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments
        
    Returns:
        Tool response dict
    """
    tool_map = {
        "create_or_update_doc": create_or_update_doc,
        "create_draft": create_draft,
    }
    
    if tool_name not in tool_map:
        return {
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(tool_map.keys()),
        }
    
    try:
        result = tool_map[tool_name](**arguments)
        return {
            "success": True,
            "data": result,
        }
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
        }


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return MCP tool definitions for the agent."""
    return [
        {
            "name": "create_or_update_doc",
            "description": "Create or update a Google Doc with the weekly pulse content. Idempotent: updates existing doc for the same week.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Document title (e.g., 'WeeklyPulse — Groww — 2026-W22')",
                    },
                    "body": {
                        "type": "string",
                        "description": "Pulse content in markdown format",
                    },
                    "week_label": {
                        "type": "string",
                        "description": "ISO week label for idempotency (e.g., '2026-W22')",
                    },
                },
                "required": ["title", "body"],
            },
        },
        {
            "name": "create_draft",
            "description": "Create a Gmail draft for the weekly pulse email. Draft-only; human must review and send.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject (e.g., 'WeeklyPulse — Groww — 2026-W22')",
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body text",
                    },
                    "doc_url": {
                        "type": "string",
                        "description": "Link to Google Doc (optional)",
                    },
                    "html": {
                        "type": "boolean",
                        "description": "Whether body is HTML (default: false)",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        },
    ]


# ── CLI Test Interface ────────────────────────────────────────────────────


def main():
    """Test the MCP server tools directly."""
    import argparse
    
    parser = argparse.ArgumentParser(description="WeeklyPulse MCP Server")
    parser.add_argument("command", choices=["test-docs", "test-gmail", "tools"])
    parser.add_argument("--title", help="Doc title for test")
    parser.add_argument("--body", help="Content for test")
    parser.add_argument("--to", help="Recipient email for test")
    parser.add_argument("--subject", help="Email subject for test")
    
    args = parser.parse_args()
    
    if args.command == "tools":
        tools = get_tool_definitions()
        print(json.dumps(tools, indent=2))
        
    elif args.command == "test-docs":
        if not args.title or not args.body:
            parser.error("--title and --body required for test-docs")
        
        result = create_or_update_doc(
            title=args.title,
            body=args.body,
            week_label="test",
        )
        print(f"Doc {result['action']}: {result['doc_url']}")
        
    elif args.command == "test-gmail":
        if not args.to or not args.subject or not args.body:
            parser.error("--to, --subject, and --body required for test-gmail")
        
        result = create_draft(
            to=args.to,
            subject=args.subject,
            body=args.body,
        )
        print(f"Draft created: {result['draft_id']}")


if __name__ == "__main__":
    main()
