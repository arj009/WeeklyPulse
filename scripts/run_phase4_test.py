"""Run Phase 4 full delivery test non-interactively."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from weeklypulse.delivery.delivery import deliver_pulse_via_mcp

# Configuration - UPDATE THIS WITH YOUR EMAIL
RECIPIENT_EMAIL = "aunkar.ranjan@gmail.com"  # ← Your Gmail account

# Test pulse content (realistic)
pulse_md = """# WeeklyPulse — Groww — 2026-W22

## Key Themes
- **Performance improvements** across all screens - app loads 40% faster
- **UI/UX enhancements** for onboarding flow - reduced drop-off by 25%
- **Critical bug fixes** for payment module - resolved transaction failures

## Top User Quotes
> "The app loads much faster now. Great work on optimization!" - User 123
> "New onboarding is so smooth! Finally completed signup on first try." - User 456
> "Payment issue fixed, thank you! Can now invest without errors." - User 789

## Sentiment Analysis
- Positive: 85% (up from 72% last week)
- Neutral: 10%
- Negative: 5% (down from 15% last week)

## Action Items
1. Continue performance optimization for search functionality
2. A/B test new onboarding variants with 50/50 split
3. Monitor payment module stability for next 2 weeks
4. Address remaining crash reports on Android 14

## Metrics
- Average rating: 4.5/5 ⭐ (up from 4.2)
- Total reviews this week: 1,234
- Response rate: 92%
- Top category: Performance (34% of reviews)
"""

# Create output directory
output_dir = Path(__file__).parent.parent / "data" / "output"
output_dir.mkdir(parents=True, exist_ok=True)
manifest_path = output_dir / "phase4-test-manifest.json"

print("=" * 60)
print("Phase 4 — Full Delivery Test")
print("=" * 60)
print(f"\nRecipient: {RECIPIENT_EMAIL}")
print(f"Week Label: 2026-W22")
print(f"App: Groww")
print(f"\nStarting delivery...\n")

# Run delivery
result = deliver_pulse_via_mcp(
    pulse_md=pulse_md,
    week_label="2026-W22",
    app_name="Groww",
    recipient=RECIPIENT_EMAIL,
    manifest_path=manifest_path,
    dry_run=False,
)

# Print results
print("\n" + "=" * 60)
print("Delivery Results")
print("=" * 60)
print(f"\nStatus: {result['delivery_status']}")
print(f"\nGoogle Doc:")
print(f"  Action: {result.get('doc_action', 'N/A')}")
print(f"  ID: {result.get('doc_id', 'N/A')}")
print(f"  URL: {result.get('doc_url', 'N/A')}")
print(f"\nGmail Draft:")
print(f"  Draft ID: {result.get('draft_id', 'N/A')}")
print(f"  To: {RECIPIENT_EMAIL}")
print(f"\nManifest: {manifest_path}")

if result.get('errors'):
    print(f"\nErrors:")
    for error in result['errors']:
        print(f"  ❌ {error}")

if result['delivery_status'] == 'complete':
    print(f"\n{'=' * 60}")
    print(f"✅ PHASE 4 DELIVERY SUCCESSFUL!")
    print(f"{'=' * 60}")
    print(f"\nNext steps:")
    print(f"  1. Open Google Doc to verify content:")
    print(f"     {result.get('doc_url', 'N/A')}")
    print(f"  2. Open Gmail → Drafts to review email")
    print(f"  3. Verify manifest at: {manifest_path}")
    print(f"  4. Send email manually (if ready)")
else:
    print(f"\n⚠️  DELIVERY {result['delivery_status'].upper()}")
    print(f"   Check errors above and troubleshoot.")
    sys.exit(1)
