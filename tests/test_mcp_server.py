"""Quick test script for Phase 4 MCP server.

Usage:
    python tests/test_mcp_server.py --test-docs
    python tests/test_mcp_server.py --test-gmail
    python tests/test_mcp_server.py --test-delivery
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_docs():
    """Test Google Docs MCP tool."""
    print("=" * 60)
    print("Testing Google Docs MCP Tool")
    print("=" * 60)
    
    from weeklypulse.delivery.mcp_google_server import _impl_create_or_update_doc
    
    title = "WeeklyPulse — MCP Test — 2026-W22"
    body = """# WeeklyPulse — MCP Test — 2026-W22

## Key Themes
- Performance improvements
- UI/UX enhancements
- Bug fixes

## Top User Quotes
> "The app is much faster now!" - User 123
> "Love the new design!" - User 456

## Action Items
- Continue performance optimization
- Address UI inconsistencies
- Fix reported bugs

## Metrics
- Average rating: 4.5/5
- Total reviews: 1,234
- Sentiment: 85% positive
"""
    
    try:
        result = _impl_create_or_update_doc(
            title=title,
            body=body,
            week_label="2026-W22",
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"   Action: {result['action']}")
        print(f"   Doc ID: {result['doc_id']}")
        print(f"   Doc URL: {result['doc_url']}")
        print(f"\n   → Open the URL to verify content")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print("\nTroubleshooting:")
        print("  1. Check Credential.json exists in project root")
        print("  2. Complete OAuth flow (browser should open)")
        print("  3. Verify Google Docs API is enabled")
        return False


def test_gmail():
    """Test Gmail MCP tool."""
    print("=" * 60)
    print("Testing Gmail MCP Tool")
    print("=" * 60)
    
    from weeklypulse.delivery.mcp_google_server import _impl_create_draft
    
    # Get recipient from user
    recipient = input("\nEnter recipient email (or press Enter for self): ").strip()
    if not recipient:
        recipient = "your-email@gmail.com"
        print(f"   Using: {recipient}")
    
    subject = "WeeklyPulse — MCP Test — 2026-W22"
    body = "This is a test email for the weekly pulse delivery.\n\nPlease verify this draft appears in Gmail."
    doc_url = "https://docs.google.com/document/d/TEST123/edit"
    
    try:
        result = _impl_create_draft(
            to=recipient,
            subject=subject,
            body=body,
            doc_url=doc_url,
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"   Draft ID: {result['draft_id']}")
        print(f"   To: {result['to']}")
        print(f"   Subject: {result['subject']}")
        print(f"\n   → Open Gmail → Drafts to verify")
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print("\nTroubleshooting:")
        print("  1. Check Credential.json exists in project root")
        print("  2. Complete OAuth flow (browser should open)")
        print("  3. Verify Gmail API is enabled")
        return False


def test_delivery():
    """Test full delivery flow."""
    print("=" * 60)
    print("Testing Full Delivery Flow")
    print("=" * 60)
    
    from weeklypulse.delivery.delivery import deliver_pulse_via_mcp
    
    pulse_md = """# WeeklyPulse — Groww — 2026-W22

## Key Themes
- Performance improvements across all screens
- UI/UX enhancements for onboarding flow
- Critical bug fixes for payment module

## Top User Quotes
> "The app loads much faster now. Great work!" - User 123
> "New onboarding is so smooth!" - User 456
> "Payment issue fixed, thank you!" - User 789

## Sentiment Analysis
- Positive: 85%
- Neutral: 10%
- Negative: 5%

## Action Items
1. Continue performance optimization for search
2. A/B test new onboarding variants
3. Monitor payment module stability
4. Address remaining crash reports

## Metrics
- Average rating: 4.5/5 ⭐
- Total reviews this week: 1,234
- Response rate: 92%
"""
    
    recipient = input("\nEnter recipient email: ").strip()
    if not recipient:
        print("❌ Recipient email required")
        return False
    
    output_dir = Path(__file__).parent.parent / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "test-delivery-manifest.json"
    
    try:
        result = deliver_pulse_via_mcp(
            pulse_md=pulse_md,
            week_label="2026-W22",
            app_name="Groww",
            recipient=recipient,
            manifest_path=manifest_path,
            dry_run=False,
        )
        
        print(f"\n{'=' * 60}")
        print(f"Delivery Result")
        print(f"{'=' * 60}")
        print(f"Status: {result['delivery_status']}")
        print(f"\nGoogle Doc:")
        print(f"  Action: {result.get('doc_action', 'N/A')}")
        print(f"  URL: {result.get('doc_url', 'N/A')}")
        print(f"\nGmail Draft:")
        print(f"  Draft ID: {result.get('draft_id', 'N/A')}")
        print(f"  To: {recipient}")
        print(f"\nManifest: {manifest_path}")
        
        if result.get('errors'):
            print(f"\nErrors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result['delivery_status'] == 'complete':
            print(f"\n✅ DELIVERY SUCCESSFUL!")
            print(f"\n   Next steps:")
            print(f"   1. Open Google Doc to verify content")
            print(f"   2. Open Gmail → Drafts to review email")
            print(f"   3. Send email manually (if ready)")
            return True
        else:
            print(f"\n⚠️  DELIVERY {result['delivery_status'].upper()}")
            print(f"   Check errors above and manifest for details")
            return False
        
    except Exception as e:
        print(f"\n❌ DELIVERY FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Phase 4 MCP Server")
    parser.add_argument("--test-docs", action="store_true", help="Test Google Docs tool")
    parser.add_argument("--test-gmail", action="store_true", help="Test Gmail tool")
    parser.add_argument("--test-delivery", action="store_true", help="Test full delivery flow")
    
    args = parser.parse_args()
    
    if not any([args.test_docs, args.test_gmail, args.test_delivery]):
        parser.print_help()
        return
    
    results = []
    
    if args.test_docs:
        results.append(("Google Docs", test_docs()))
    
    if args.test_gmail:
        results.append(("Gmail", test_gmail()))
    
    if args.test_delivery:
        results.append(("Full Delivery", test_delivery()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
