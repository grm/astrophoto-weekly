#!/usr/bin/env python3
"""Verify four distinct Discord destinations, then send clearly labelled setup tests."""
import json
import os
import urllib.error
import urllib.request

from discord import post_message
from specialist import series_config


def main():
    destinations = {}
    problems = []
    configs = series_config()
    checks = [('general', {'webhook_secret': 'DISCORD_WEBHOOK_URL'})] + list(configs.items())
    for series, config in checks:
        webhook = os.environ.get(config['webhook_secret'], '').strip()
        if not webhook:
            if series != 'general':
                problems.append(f"{config['webhook_secret']} is missing")
            continue
        try:
            req = urllib.request.Request(webhook, headers={'User-Agent': 'AstroPhotoWeeklySetup/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                channel = json.load(response).get('channel_id')
            if not channel or channel in destinations.values():
                problems.append(f'{series}: missing or duplicate Discord channel')
            destinations[series] = channel
            print(f'{series}: webhook reachable; destination {channel}')
        except urllib.error.HTTPError as exc:
            problems.append(f'{series}: Discord HTTP {exc.code}')
        except (OSError, ValueError):
            problems.append(f'{series}: webhook verification unavailable')
    if problems:
        for problem in problems:
            print(f'::error::{problem}')
        raise SystemExit(1)
    if os.environ.get('SEND_SETUP_TESTS') != 'true':
        return
    failed = False
    for series, config in configs.items():
        try:
            result = post_message(os.environ[config['webhook_secret']],
                f"🧪 **Test de connexion — {config['title']}**\n\n"
                "Ce salon recevra sa newsletter dédiée tous les quinze jours, lorsque la matière le mérite. "
                "La veille est hebdomadaire ; aucune édition n’a été publiée par ce test.\n\n"
                "📡 Le bon logiciel, le bon salon : connexion établie !")
            print(f"{series}: test acknowledged in channel {result['channel_id']}, message {result['message_id']}")
        except (ValueError, RuntimeError, OSError) as exc:
            failed = True
            print(f'::error::{series}: {exc}. Inspect the channel before rerunning tests.')
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
