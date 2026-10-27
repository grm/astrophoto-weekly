#!/usr/bin/env python3
"""Validate specialist submissions without touching the generalist publication."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def series_config(root=ROOT):
    return json.loads((root / "data/specialists/series.json").read_text(encoding="utf-8"))


def publish(path: Path, root=ROOT):
    relative = path.relative_to(root).as_posix()
    match = re.fullmatch(r"data/specialists/submissions/([a-z-]+)/([0-9]{3})\.json", relative)
    if not match or match[1] not in series_config(root):
        raise ValueError("Unknown specialist submission path")
    series, slug = match.groups()
    number = int(slug)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"issue", "digest", "topics"}:
        raise ValueError("Expected issue, digest and topics")
    issue, digest, topics = (payload[key] for key in ("issue", "digest", "topics"))
    if not isinstance(issue, str) or not isinstance(digest, str) or not isinstance(topics, dict):
        raise ValueError("Invalid payload types")
    if not 300 <= len(issue) <= 150000 or not 1 <= len(digest) < 2000 or "[URL]" not in digest:
        raise ValueError("Invalid lengths or missing digest URL placeholder")
    front = re.match(r"\A---\n(.*?)\n---\n", issue, re.S)
    if not front:
        raise ValueError("Missing YAML front matter")
    header = front[1]
    import yaml
    try:
        metadata = yaml.safe_load(header)
    except yaml.YAMLError:
        raise ValueError("Invalid YAML front matter") from None
    if not isinstance(metadata, dict) or metadata.get("series") != series or metadata.get("number") != number:
        raise ValueError("Invalid front matter identity")
    if not all(isinstance(metadata.get(key), str) and metadata[key].strip() for key in ("title", "description")):
        raise ValueError("Invalid front matter text")
    if not isinstance(metadata.get("tags"), list) or not all(isinstance(tag, str) for tag in metadata["tags"]):
        raise ValueError("Invalid tags")
    if not re.search(rf"(?m)^number:\s*{number}\s*$", header):
        raise ValueError("Issue number mismatch")
    if not re.search(rf'(?m)^series:\s*[\"\x27]?{re.escape(series)}[\"\x27]?\s*$', header):
        raise ValueError("Series mismatch")
    for key in ("date", "title", "description", "tags"):
        if not re.search(rf"(?m)^{key}:\s*\S", header):
            raise ValueError(f"Missing front matter {key}")
    date_match = re.search(r'(?m)^date:\s*[\"\x27]?(\d{4}-\d{2}-\d{2})[\"\x27]?\s*$', header)
    if not date_match:
        raise ValueError("Invalid date")
    dt.date.fromisoformat(date_match[1])
    if not 1 <= len(topics) <= 20:
        raise ValueError("Expected 1–20 editorial topics")
    for key, topic in topics.items():
        if (not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key)
                or not isinstance(topic, dict) or topic.get("issue") != number
                or topic.get("date") != date_match[1]
                or not re.match(r"https?://\S+$", str(topic.get("source", "")))
                or not topic.get("status") or not topic.get("angle")):
            raise ValueError("Invalid editorial topic")
    issues = root / "content/specialists/issues" / series
    issue_path = issues / f"{slug}.md"
    digest_path = root / "content/specialists/digests" / series / f"{slug}.md"
    history_path = root / "data/specialists" / series / "editorial-history.json"
    if issue_path.exists() or digest_path.exists():
        if (issue_path.exists() and digest_path.exists()
                and issue_path.read_text(encoding="utf-8") == issue.rstrip() + "\n"
                and digest_path.read_text(encoding="utf-8") == digest.rstrip() + "\n"):
            return None
        raise ValueError("Issue or digest already exists with different content")
    existing = [int(p.stem) for p in issues.glob("[0-9][0-9][0-9].md")]
    if number != max(existing, default=0) + 1:
        raise ValueError("Not the next issue for this series")
    history = json.loads(history_path.read_text(encoding="utf-8"))
    if set(topics).intersection(history["topics"]):
        raise ValueError("Duplicate topic within this series")
    history["last_issue"] = number
    history["topics"].update(topics)
    # The workflow commits all three files together, only after every check above.
    issue_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    issue_path.write_text(issue.rstrip() + "\n", encoding="utf-8")
    digest_path.write_text(digest.rstrip() + "\n", encoding="utf-8")
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"series": series, "slug": slug}
