#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from specialist import series_config

ROOT = Path(__file__).resolve().parents[1]
SITE = json.loads((ROOT / 'data/site.json').read_text(encoding='utf-8'))


def destination(series):
    if series == 'general':
        return 'DISCORD_WEBHOOK_URL'
    config = series_config(ROOT)
    if series not in config:
        raise ValueError('Unknown newsletter series')
    return config[series]['webhook_secret']


def send(series, slug):
    if not re.fullmatch(r'[0-9]{3}', slug):
        raise ValueError('Invalid issue number')
    secret = destination(series)
    webhook = os.environ.get(secret, '').strip()
    if not webhook:
        raise ValueError(f'{secret} is not configured')
    # A specialist may never silently use the generalist webhook.
    if series == 'general':
        digest_path = ROOT / 'content/digests' / f'{slug}.md'
        issue_path = f'issues/{slug}/'
    else:
        digest_path = ROOT / 'content/specialists/digests' / series / f'{slug}.md'
        issue_path = f'veilles/{series}/{slug}/'
    page_url = os.environ.get('PAGE_URL', SITE['site_url']).rstrip('/')
    content = digest_path.read_text(encoding='utf-8').replace('[URL]', f'{page_url}/{issue_path}').strip()
    if len(content.encode('utf-16-le')) // 2 > 2000:
        raise ValueError('Discord digest exceeds 2000 UTF-16 code units after URL expansion')
    return post_message(webhook, content)


def post_message(webhook, content):
    parts = urllib.parse.urlsplit(webhook)
    if parts.scheme != 'https' or parts.hostname not in {'discord.com', 'discordapp.com'} or not re.fullmatch(r'/api(?:/v\d+)?/webhooks/\d+/[^/]+', parts.path):
        raise ValueError('Invalid Discord incoming webhook URL')
    query = urllib.parse.parse_qs(parts.query)
    query['wait'] = ['true']
    url = urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query, doseq=True)))
    payload = json.dumps({'content': content, 'allowed_mentions': {'parse': []}}, ensure_ascii=False).encode('utf-8')
    request = urllib.request.Request(url, data=payload, headers={
        'Content-Type': 'application/json', 'User-Agent': 'AstroPhotoWeekly/1.0',
    }, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not print exceptions containing webhook URLs/tokens.
        raise RuntimeError(f'Discord HTTP {exc.code}; delivery requires inspection') from None
    except (OSError, ValueError):
        raise RuntimeError('Discord response unavailable; delivery is uncertain; do not retry automatically') from None
    if not result.get('id') or not result.get('channel_id'):
        raise RuntimeError('Discord acknowledgement missing; delivery requires inspection')
    return {'message_id': result['id'], 'channel_id': result['channel_id']}


if __name__ == '__main__':
    result = send(os.environ.get('NEWSLETTER_SERIES', 'general'), os.environ.get('ISSUE_SLUG', ''))
    print(f"Discord acknowledged message {result['message_id']}")
