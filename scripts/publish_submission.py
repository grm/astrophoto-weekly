#!/usr/bin/env python3
"""Validate and atomically publish one staged newsletter issue."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"data/submissions/[0-9]{3}\.json", sys.argv[1]):
        raise SystemExit("Expected numbered submission path")
    path = ROOT / sys.argv[1]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"issue", "digest", "topics"}:
        raise SystemExit("Expected issue, digest and topics")
    slug = path.stem
    number = int(slug)
    issue, digest, topics = payload["issue"], payload["digest"], payload["topics"]
    if not isinstance(issue, str) or not isinstance(digest, str) or not isinstance(topics, dict):
        raise SystemExit("Invalid payload types")
    if not 300 <= len(issue) <= 150000 or not 1 <= len(digest) <= 2000:
        raise SystemExit("Invalid issue or digest length")
    if not issue.startswith("---\n") or not re.search(rf"(?m)^number:\s*{number}\s*$", issue):
        raise SystemExit("Invalid issue number")
    if not all(re.search(rf"(?m)^{key}:", issue) for key in ("date", "title", "description", "tags")):
        raise SystemExit("Missing front matter")
    if not 1 <= len(topics) <= 20 or not all(isinstance(k,str) and isinstance(v,dict) and v.get("issue")==number and v.get("source") for k,v in topics.items()):
        raise SystemExit("Invalid editorial topics")
    issues = ROOT / "content/issues"
    existing = [int(p.stem) for p in issues.glob("[0-9][0-9][0-9].md")]
    if number != max(existing, default=0) + 1:
        raise SystemExit("Not the next issue")
    issue_path = issues / f"{slug}.md"
    digest_path = ROOT / "content/digests" / f"{slug}.md"
    if issue_path.exists() or digest_path.exists():
        raise SystemExit("Issue or digest already exists")
    history_path = ROOT / "data/editorial-history.json"
    history = json.loads(history_path.read_text(encoding="utf-8"))
    if set(topics).intersection(history["topics"]):
        raise SystemExit("Duplicate editorial topic keys")
    history["last_issue"] = number
    history["topics"].update(topics)
    digest_path.write_text(digest.rstrip()+"\n", encoding="utf-8")
    history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    issue_path.write_text(issue.rstrip()+"\n", encoding="utf-8")
    print(f"Prepared issue {slug}")

if __name__ == "__main__":
    main()
