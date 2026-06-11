"""WeeklyPulse Delivery Module — MCP-based delivery to Google Docs and Gmail.

This module orchestrates the delivery of validated weekly pulses to:
1. Google Docs (full pulse content)
2. Gmail (draft with teaser + doc link)

Delivery follows the sequence defined in ADR-013:
- PII gate verification
- Docs MCP call (create/update)
- Gmail MCP call (draft creation)
- Manifest update

References:
- ADR-008: Doc canonical; email teaser + link
- ADR-010: Draft-only; human sends
- ADR-013: Docs before Gmail delivery order
- ADR-019: Same-week re-run idempotency
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def deliver_pulse_via_mcp(
    pulse_md: str,
    week_label: str,
    app_name: str,
    recipient: str,
    manifest_path: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Deliver a validated weekly pulse via MCP server.
    
    Args:
        pulse_md: Full pulse content in markdown (PII-scrubbed)
        week_label: ISO week label (e.g., "2026-W22")
        app_name: App name for title (e.g., "Groww")
        recipient: Email address for Gmail draft
        manifest_path: Path to manifest.json for delivery status
        dry_run: If True, log actions without calling MCP
        
    Returns:
        Dict with delivery status, doc_url, draft_id, and action taken
    """
    title = f"WeeklyPulse — {app_name} — {week_label}"
    subject = title
    
    result = {
        "week_label": week_label,
        "delivery_status": "pending",
        "doc_url": None,
        "doc_id": None,
        "doc_action": None,
        "draft_id": None,
        "errors": [],
    }
    
    try:
        # Step 1: PII gate re-confirmation (checked before calling this function)
        logger.info(f"Starting delivery for {title}")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would create/update doc: {title}")
            logger.info(f"[DRY RUN] Would create draft to: {recipient}")
            result["delivery_status"] = "dry_run"
            return result
        
        # Step 2: Create or update Google Doc
        logger.info("Calling MCP: create_or_update_doc")
        doc_result = _call_mcp_create_doc(
            title=title,
            body=pulse_md,
            week_label=week_label,
        )
        
        result["doc_id"] = doc_result.get("doc_id")
        result["doc_url"] = doc_result.get("doc_url")
        result["doc_action"] = doc_result.get("action")  # "created" or "updated"
        
        if not result["doc_url"]:
            raise RuntimeError("Doc creation failed: no doc_url returned")
        
        logger.info(f"Doc {result['doc_action']}: {result['doc_url']}")
        
        # Step 3: Create Gmail draft (per ADR-008: teaser + link)
        logger.info("Calling MCP: create_draft")
        teaser = _generate_email_teaser(pulse_md)
        draft_result = _call_mcp_create_draft(
            to=recipient,
            subject=subject,
            body=teaser,
            doc_url=result["doc_url"],
        )
        
        result["draft_id"] = draft_result.get("draft_id")
        
        if not result["draft_id"]:
            raise RuntimeError("Draft creation failed: no draft_id returned")
        
        logger.info(f"Draft created: {result['draft_id']}")
        
        # Step 4: Mark delivery as complete
        result["delivery_status"] = "complete"
        logger.info(f"Delivery complete for {title}")
        
    except Exception as e:
        logger.error(f"Delivery failed: {e}")
        result["delivery_status"] = _classify_error(e, result)
        result["errors"].append(str(e))
    
    finally:
        # Step 5: Update manifest
        _update_manifest(manifest_path, result)
    
    return result


def _call_mcp_create_doc(title: str, body: str, week_label: str) -> dict[str, Any]:
    """Call MCP server to create or update Google Doc.
    
    TODO: Implement actual MCP client call.
    For now, calls the implementation function directly.
    """
    # Import here to avoid circular imports
    from weeklypulse.delivery.mcp_google_server import _impl_create_or_update_doc
    
    return _impl_create_or_update_doc(
        title=title,
        body=body,
        week_label=week_label,
    )


def _call_mcp_create_draft(
    to: str,
    subject: str,
    body: str,
    doc_url: str,
) -> dict[str, Any]:
    """Call MCP server to create Gmail draft.
    
    TODO: Implement actual MCP client call.
    For now, calls the implementation function directly.
    """
    # Import here to avoid circular imports
    from weeklypulse.delivery.mcp_google_server import _impl_create_draft
    
    return _impl_create_draft(
        to=to,
        subject=subject,
        body=body,
        doc_url=doc_url,
    )


def _generate_email_teaser(pulse_md: str, max_lines: int = 10) -> str:
    """Generate a hybrid email teaser from pulse content.
    
    Per ADR-008 (updated), email contains:
    - Key themes
    - Top quotes (2-3)
    - Action items
    - Link to full doc for details
    
    Args:
        pulse_md: Full pulse markdown content
        max_lines: Maximum number of lines per section
        
    Returns:
        Hybrid teaser text with key sections
    """
    lines = pulse_md.strip().split("\n")
    
    email_sections = []
    
    # Track which section we're in
    current_section = None
    section_content = []
    
    for line in lines:
        stripped = line.strip()
        
        # Detect section headers (## or ###)
        if stripped.startswith("## "):
            # Save previous section if it had content
            if current_section and section_content:
                email_sections.append((current_section, section_content[:max_lines]))
            
            current_section = stripped[3:]  # Remove "## "
            section_content = []
        elif stripped.startswith("### "):
            # Save previous section if it had content
            if current_section and section_content:
                email_sections.append((current_section, section_content[:max_lines]))
            
            current_section = stripped[4:]  # Remove "### "
            section_content = []
        elif stripped and current_section:
            section_content.append(stripped)
    
    # Add last section
    if current_section and section_content:
        email_sections.append((current_section, section_content[:max_lines]))
    
    # Build email body
    email_body = []
    
    # Include ALL sections (full pulse content in email)
    for section_name, section_lines in email_sections:
        email_body.append(f"\n{section_name.upper()}")
        email_body.append("=" * len(section_name))
        
        for line in section_lines:
            # Skip empty lines at start
            if line:
                email_body.append(line)
    
    # Add doc link at the end
    email_body.append("\n" + "=" * 50)
    email_body.append("📄 View full pulse with formatting and metrics in Google Docs:")
    
    return "\n".join(email_body)


def _classify_error(error: Exception, result: dict[str, Any]) -> str:
    """Classify error to determine delivery status.
    
    Args:
        error: The exception that occurred
        result: Current delivery result dict
        
    Returns:
        Status string: "partial", "failed", or "blocked_pii"
    """
    error_msg = str(error).lower()
    
    # Doc succeeded, draft failed
    if result.get("doc_url") and "draft" in error_msg:
        return "partial"
    
    # PII detected
    if "pii" in error_msg:
        return "blocked_pii"
    
    # Doc failed
    if not result.get("doc_url"):
        return "failed"
    
    # Unknown error after doc success
    return "partial"


def _update_manifest(manifest_path: Path, result: dict[str, Any]):
    """Update manifest.json with delivery status.
    
    Args:
        manifest_path: Path to manifest.json
        result: Delivery result dict
    """
    if not manifest_path.exists():
        logger.warning(f"Manifest not found at {manifest_path}, creating new")
        manifest = {"week_label": result["week_label"]}
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    # Update delivery section
    manifest["delivery"] = {
        "status": result["delivery_status"],
        "doc_url": result["doc_url"],
        "doc_id": result["doc_id"],
        "doc_action": result["doc_action"],
        "draft_id": result["draft_id"],
        "errors": result["errors"],
    }
    
    # Write back
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info(f"Manifest updated: {manifest_path}")
