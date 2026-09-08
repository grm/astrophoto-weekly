#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import os
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))


def main() -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    issue_slug = os.environ.get("ISSUE_SLUG", "").strip()

    if not webhook_url:
        print("DISCORD_WEBHOOK_URL is not configured; skipping notification.")
        return
    if not issue_slug:
        print("ISSUE_SLUG is missing; skipping notification.")
        return

    digest_path = ROOT / "content" / "digests" / f"{issue_slug}.md"
    if not digest_path.exists():
        raise SystemExit(f"Missing Discord digest: {digest_path}")

    page_url = os.environ.get("PAGE_URL", SITE["site_url"]).rstrip("/")
    issue_url = f"{page_url}/issues/{issue_slug}/"
    content = digest_path.read_text(encoding="utf-8").replace("[URL]", issue_url).strip()

    if len(content) > 2000:
        raise SystemExit("Discord digest exceeds the 2000-character message limit")

    payload = json.dumps(
        {"content": content, "allowed_mentions": {"parse": []}},
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AstroPhotoWeekly/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status not in (200, 204):
            raise SystemExit(f"Discord returned HTTP {response.status}")

    print(f"Discord digest for issue #{issue_slug} sent successfully.")


if __name__ == "__main__":
    main()
