#!/usr/bin/env python3
"""Drain pending submissions and preserve a durable Discord outbox."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from specialist import publish

ROOT = Path(__file__).resolve().parents[1]


def main():
    outbox_path = ROOT / "data/discord-outbox.json"
    outbox = json.loads(outbox_path.read_text(encoding="utf-8"))
    errors = []
    published = []
    # Drain current main, not just the triggering commit: queued runs can be coalesced.
    paths = sorted((ROOT / "data/submissions").glob("[0-9][0-9][0-9].json"))
    paths += sorted((ROOT / "data/specialists/submissions").glob("*/*.json"))
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        try:
            if relative.startswith("data/submissions/"):
                if not re.fullmatch(r"[0-9]{3}", path.stem):
                    raise ValueError("Invalid generalist issue number")
                if (ROOT / "content/issues" / f"{path.stem}.md").exists():
                    continue  # Previously published issues never enter the new outbox.
                result = subprocess.run([sys.executable, "scripts/publish_submission.py", relative],
                                        cwd=ROOT, capture_output=True, text=True)
                if result.returncode:
                    raise ValueError(result.stderr.strip() or result.stdout.strip())
                entry = {"series": "general", "slug": path.stem}
            else:
                entry = publish(path)
            if entry is not None:
                published.append(entry)
                if not any((m["series"], m["slug"]) == (entry["series"], entry["slug"]) for m in outbox["messages"]):
                    outbox["messages"].append({**entry, "status": "pending"})
        except (ValueError, KeyError, TypeError, OSError) as exc:
            # An invalid specialist submission must not stop the generalist or other series.
            errors.append(relative)
            print(f"::warning file={relative}::Submission rejected: {exc}")
    outbox_path.write_text(json.dumps(outbox, indent=2) + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"has_pending={'true' if [m for m in outbox['messages'] if m['status'] in {'pending', 'blocked'}] else 'false'}\n")
            output.write(f"has_errors={'true' if errors else 'false'}\n")
    print(f"Prepared {len(published)} issue(s).")


if __name__ == "__main__":
    main()
