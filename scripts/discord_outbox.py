#!/usr/bin/env python3
"""Reserve attempts durably before sending; uncertain deliveries are never auto-retried."""
import json
import os
from pathlib import Path
import sys

from discord import destination, send

ROOT = Path(__file__).resolve().parents[1]
OUTBOX = ROOT / 'data/discord-outbox.json'


def main():
    box = json.loads(OUTBOX.read_text(encoding='utf-8'))
    batch_file = Path(os.environ['BATCH_FILE'])
    if sys.argv[1] == 'reserve':
        batch = []
        for message in box['messages']:
            if message['status'] not in {'pending', 'blocked'}:
                continue
            if not os.environ.get(destination(message['series']), '').strip():
                message['status'] = 'blocked'
                print(f"::warning::Missing destination for {message['series']} #{message['slug']}")
                continue
            message['status'] = 'sending'
            batch.append({'series': message['series'], 'slug': message['slug']})
        batch_file.write_text(json.dumps(batch), encoding='utf-8')
        OUTBOX.write_text(json.dumps(box, indent=2) + '\n', encoding='utf-8')
        print(f'Reserved {len(batch)} notification(s). Existing sending/uncertain records need manual inspection.')
    elif sys.argv[1] == 'send':
        failures = sum(message['status'] == 'blocked' for message in box['messages'])
        for entry in json.loads(batch_file.read_text(encoding='utf-8')):
            message = next(m for m in box['messages'] if (m['series'], m['slug']) == (entry['series'], entry['slug']))
            try:
                message.update(send(entry['series'], entry['slug']))
                message['status'] = 'sent'
                print(f"Delivered {entry['series']} #{entry['slug']}; acknowledgement recorded.")
            except (ValueError, OSError, RuntimeError) as exc:
                message['status'] = 'uncertain'
                failures += 1
                print(f"::error::Delivery requires inspection for {entry['series']} #{entry['slug']}: {exc}")
            OUTBOX.write_text(json.dumps(box, indent=2) + '\n', encoding='utf-8')
        if failures:
            raise SystemExit(1)
    else:
        raise SystemExit('Expected reserve or send')


if __name__ == '__main__':
    main()
