#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path
import json
import re
import shutil
import xml.etree.ElementTree as ET

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
ISSUES_DIR = ROOT / "content" / "issues"
OUTPUT_DIR = ROOT / "_site"
ASSETS_DIR = ROOT / "assets"
SITE = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
BASE_URL = SITE["site_url"].rstrip("/")


def parse_issue(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not match:
        raise ValueError(f"Missing YAML front matter in {path}")

    metadata = yaml.safe_load(match.group(1)) or {}
    body = match.group(2)
    for key in ("number", "date", "title"):
        if key not in metadata:
            raise ValueError(f"Missing {key!r} in {path}")

    metadata["number"] = int(metadata["number"])
    if isinstance(metadata["date"], date):
        metadata["date"] = metadata["date"].isoformat()
    metadata["slug"] = f"{metadata['number']:03d}"
    metadata["url"] = f"{BASE_URL}/issues/{metadata['slug']}/"
    metadata["html"] = markdown.markdown(
        body,
        extensions=["extra", "sane_lists", "smarty"],
        output_format="html5",
    )
    return metadata


def page(title: str, body: str, description: str | None = None) -> str:
    description = description or SITE["description"]
    return f'''<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{escape(title)} · {escape(SITE['title'])}</title>
  <meta name="description" content="{escape(description)}">
  <link rel="stylesheet" href="{BASE_URL}/assets/style.css">
  <link rel="alternate" type="application/rss+xml" title="{escape(SITE['title'])}" href="{BASE_URL}/feed.xml">
</head>
<body>
<header class="container">
  <div class="brand"><a href="{BASE_URL}/">🌌 {escape(SITE['title'])}</a></div>
  <p class="tagline">{escape(SITE['description'])}</p>
</header>
<main class="container">{body}</main>
<footer><div class="container">AstroPhoto Weekly · étoiles rondes non garanties.</div></footer>
</body>
</html>'''


def build_feed(issues: list[dict]) -> None:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = SITE["title"]
    ET.SubElement(channel, "link").text = f"{BASE_URL}/"
    ET.SubElement(channel, "description").text = SITE["description"]
    ET.SubElement(channel, "language").text = "fr"

    for issue in sorted(issues, key=lambda item: item["number"], reverse=True)[:30]:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = issue["title"]
        ET.SubElement(item, "link").text = issue["url"]
        ET.SubElement(item, "guid").text = issue["url"]
        ET.SubElement(item, "description").text = issue.get("description", "")

    ET.ElementTree(rss).write(OUTPUT_DIR / "feed.xml", encoding="utf-8", xml_declaration=True)


def main() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)
    shutil.copytree(ASSETS_DIR, OUTPUT_DIR / "assets")

    issues = [parse_issue(path) for path in sorted(ISSUES_DIR.glob("*.md"))]

    for issue in issues:
        target = OUTPUT_DIR / "issues" / issue["slug"]
        target.mkdir(parents=True)
        body = (
            f'<article><p class="meta">Édition #{issue["slug"]} · {escape(str(issue["date"]))}</p>'
            f'{issue["html"]}</article>'
        )
        (target / "index.html").write_text(
            page(issue["title"], body, issue.get("description")), encoding="utf-8"
        )

    if issues:
        latest = max(issues, key=lambda item: item["number"])
        cards = "".join(
            f'''<section class="card">
<span class="badge">#{issue['slug']}</span>
<h2><a href="{issue['url']}">{escape(issue['title'])}</a></h2>
<p class="meta">{escape(str(issue['date']))}</p>
<p>{escape(issue.get('description', ''))}</p>
</section>'''
            for issue in sorted(issues, key=lambda item: item["number"], reverse=True)
        )
        home = f'''<section class="card">
<span class="badge">Dernière édition</span>
<h1><a href="{latest['url']}">{escape(latest['title'])}</a></h1>
<p>{escape(latest.get('description', ''))}</p>
</section>
<h2>Archives</h2>
{cards}'''
        (OUTPUT_DIR / "latest.json").write_text(
            json.dumps(
                {key: latest[key] for key in ("number", "slug", "title", "date", "url")},
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
    else:
        home = '''<section class="card">
<span class="badge">Bientôt</span>
<h1>AstroPhoto Weekly prépare sa première orbite.</h1>
<p>La première édition francophone sera publiée ici. La veille est en cours ; les câbles USB sont priés de rester coopératifs.</p>
</section>'''

    (OUTPUT_DIR / "index.html").write_text(
        page(SITE["title"], home, SITE["description"]), encoding="utf-8"
    )
    (OUTPUT_DIR / ".nojekyll").write_text("", encoding="utf-8")
    build_feed(issues)


if __name__ == "__main__":
    main()
