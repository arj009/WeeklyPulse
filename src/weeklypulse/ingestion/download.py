"""Download public store reviews into data/raw CSV (Play + App Store)."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from weeklypulse.config import REPO_ROOT

DEFAULT_PLAY_PACKAGE = "com.nextbillion.groww"
DEFAULT_APP_STORE_ID = "1404871703"  # Groww — Stocks, Mutual Fund, IPO (IN)
DEFAULT_COUNTRY = "in"
DEFAULT_LANG = "en"


def _fetch_url(url: str) -> dict[str, Any]:
    req = Request(url, headers={"User-Agent": "WeeklyPulse/1.0"})
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_play_reviews(
    package: str,
    count: int,
    lang: str,
    country: str,
) -> list[dict[str, Any]]:
    from google_play_scraper import Sort, reviews

    batch_size = min(200, count)
    collected: list[dict[str, Any]] = []
    token = None

    while len(collected) < count:
        need = min(batch_size, count - len(collected))
        batch, token = reviews(
            package,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=need,
            continuation_token=token,
        )
        if not batch:
            break
        collected.extend(batch)
        if token is None:
            break

    return collected[:count]


def write_play_csv(rows: list[dict[str, Any]], path: Path, package: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "Package Name",
                "Review Submit Date and Time",
                "Star Rating",
                "Review Title",
                "Review Text",
            ],
        )
        writer.writeheader()
        for r in rows:
            at = r.get("at")
            if isinstance(at, datetime):
                if at.tzinfo is None:
                    at = at.replace(tzinfo=timezone.utc)
                dt_str = at.strftime("%Y-%m-%d %H:%M:%S")
            else:
                dt_str = str(at) if at else ""
            writer.writerow(
                {
                    "Package Name": package,
                    "Review Submit Date and Time": dt_str,
                    "Star Rating": r.get("score", ""),
                    "Review Title": (r.get("title") or "")[:500],
                    "Review Text": (r.get("content") or "")[:8000],
                }
            )
    return len(rows)


def download_app_store_reviews(
    app_id: str,
    count: int,
    country: str,
) -> list[dict[str, Any]]:
    """Fetch via public iTunes RSS customer reviews feed."""
    collected: list[dict[str, Any]] = []
    page = 1
    max_pages = max(1, (count // 50) + 2)

    while len(collected) < count and page <= max_pages:
        url = (
            f"https://itunes.apple.com/{country}/rss/customerreviews/"
            f"id={app_id}/sortBy=mostRecent/page={page}/json"
        )
        try:
            data = _fetch_url(url)
        except (HTTPError, URLError, json.JSONDecodeError):
            break

        entries = data.get("feed", {}).get("entry", [])
        if not entries:
            break
        # First entry on page 1 can be app metadata, not a review
        start = 1 if page == 1 and entries and "im:rating" not in entries[0] else 0
        for entry in entries[start:]:
            if len(collected) >= count:
                break
            rating = entry.get("im:rating", {}).get("label")
            title = entry.get("title", {}).get("label", "")
            text = entry.get("content", {}).get("label", "")
            updated = entry.get("updated", {}).get("label", "")
            if rating is None:
                continue
            collected.append(
                {
                    "rating": rating,
                    "title": title if title != text else "",
                    "text": text,
                    "updated": updated,
                }
            )
        page += 1

    return collected[:count]


def write_app_store_csv(rows: list[dict[str, Any]], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Date", "Rating", "Review Title", "Review"],
        )
        writer.writeheader()
        for r in rows:
            updated = r.get("updated", "")
            if updated and "T" in updated:
                try:
                    dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                    date_str = dt.strftime("%Y-%m-%d")
                except ValueError:
                    date_str = updated[:10]
            else:
                date_str = (updated or "")[:10]
            writer.writerow(
                {
                    "Date": date_str,
                    "Rating": r.get("rating", ""),
                    "Review Title": (r.get("title") or "")[:500],
                    "Review": (r.get("text") or "")[:8000],
                }
            )
    return len(rows)


def run_download(cfg: dict[str, Any], count: int | None = None) -> dict[str, Any]:
    dl = cfg.get("download", {})
    ing = cfg["ingestion"]
    raw_dir = REPO_ROOT / ing["raw_input_dir"]

    play_package = dl.get("play_package", DEFAULT_PLAY_PACKAGE)
    app_store_id = str(dl.get("app_store_id", DEFAULT_APP_STORE_ID))
    country = dl.get("country", DEFAULT_COUNTRY)
    lang = dl.get("lang", DEFAULT_LANG)
    per_platform = count or int(dl.get("count_per_platform", ing.get("max_reviews", 1000)))

    play_path = raw_dir / "play_store_reviews.csv"
    ios_path = raw_dir / "app_store_reviews.csv"

    play_rows = download_play_reviews(play_package, per_platform, lang, country)
    play_written = write_play_csv(play_rows, play_path, play_package)

    ios_rows = download_app_store_reviews(app_store_id, per_platform, country)
    ios_written = write_app_store_csv(ios_rows, ios_path)

    return {
        "play_store": {"path": str(play_path.relative_to(REPO_ROOT)), "downloaded": play_written},
        "app_store": {"path": str(ios_path.relative_to(REPO_ROOT)), "downloaded": ios_written},
        "count_requested_per_platform": per_platform,
    }
