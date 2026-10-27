import copy
import io
import urllib.error
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import specialist
import discord
import discord_outbox

REPO = Path(__file__).resolve().parents[1]


def payload(series='pixinsight', number=1):
    return {
        'issue': f'---\nseries: {series}\nnumber: {number}\ndate: 2026-10-30\ntitle: "Une nouveauté utile"\ndescription: "Un changement documenté"\ntags: [traitement]\n---\n\n' + 'Explication sourcée. ' * 30,
        'digest': 'Une nouveauté utile : [URL]',
        'topics': {'same-news': {'issue': number, 'date': '2026-10-30', 'status': 'stable', 'version': '1.0', 'source': 'https://example.org/release', 'angle': 'Practical impact'}},
    }


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for relative in ['data/specialists/series.json', 'data/editorial-history.json', 'data/discord-outbox.json']:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text((REPO / relative).read_text())
        self.original_general = (self.root / 'data/editorial-history.json').read_bytes()
        for series in specialist.series_config(self.root):
            path = self.root / 'data/specialists' / series / 'editorial-history.json'
            path.parent.mkdir(parents=True)
            path.write_text('{"last_issue":0,"topics":{}}')

    def submit(self, series, body=None, slug='001'):
        path = self.root / 'data/specialists/submissions' / series / f'{slug}.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload(series) if body is None else body))
        return path

    def test_same_news_allowed_in_each_series_without_touching_generalist(self):
        for series in specialist.series_config(self.root):
            result = specialist.publish(self.submit(series), self.root)
            self.assertEqual(result, {'series': series, 'slug': '001'})
            history = json.loads((self.root / 'data/specialists' / series / 'editorial-history.json').read_text())
            self.assertIn('same-news', history['topics'])
        self.assertEqual(self.original_general, (self.root / 'data/editorial-history.json').read_bytes())

    def test_replay_does_not_publish_again(self):
        path = self.submit('pixinsight')
        specialist.publish(path, self.root)
        self.assertIsNone(specialist.publish(path, self.root))

    def test_duplicate_in_same_series_rejected_before_writing(self):
        specialist.publish(self.submit('pixinsight'), self.root)
        body = payload('pixinsight', 2)
        with self.assertRaisesRegex(ValueError, 'Duplicate topic'):
            specialist.publish(self.submit('pixinsight', body, '002'), self.root)
        self.assertFalse((self.root / 'content/specialists/issues/pixinsight/002.md').exists())

    def test_cross_series_payload_and_bad_yaml_rejected(self):
        for body in [payload('nina'), {**payload(), 'issue': payload()['issue'].replace('tags: [traitement]', 'tags: [broken')}]:
            with self.assertRaises(ValueError):
                specialist.publish(self.submit('pixinsight', body), self.root)
        self.assertEqual(self.original_general, (self.root / 'data/editorial-history.json').read_bytes())

    def test_bad_specialist_does_not_block_valid_general_or_specialist(self):
        scripts = self.root / 'scripts'
        scripts.mkdir()
        for name in ['specialist.py', 'process_submissions.py', 'publish_submission.py']:
            (scripts / name).write_bytes((REPO / 'scripts' / name).read_bytes())
        self.submit('pixinsight', {'broken': True})
        self.submit('siril')
        general = payload(number=9)
        general['issue'] = general['issue'].replace('series: pixinsight\n', '')
        target = self.root / 'data/submissions/009.json'
        target.parent.mkdir()
        target.write_text(json.dumps(general))
        (self.root / 'content/issues').mkdir(parents=True)
        (self.root / 'content/digests').mkdir(parents=True)
        (self.root / 'content/issues/008.md').write_text('Existing issue')
        result = subprocess.run([sys.executable, 'scripts/process_submissions.py'], cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / 'content/issues/009.md').exists())
        self.assertTrue((self.root / 'content/specialists/issues/siril/001.md').exists())
        self.assertFalse((self.root / 'content/specialists/issues/pixinsight/001.md').exists())
        box = json.loads((self.root / 'data/discord-outbox.json').read_text())
        self.assertEqual({m['series'] for m in box['messages']}, {'general', 'siril'})
        again = subprocess.run([sys.executable, 'scripts/process_submissions.py'], cwd=self.root, capture_output=True)
        self.assertEqual(again.returncode, 0)
        self.assertEqual(box, json.loads((self.root / 'data/discord-outbox.json').read_text()))

    def test_specialist_destination_never_falls_back_to_generalist(self):
        with patch.dict(os.environ, {'DISCORD_WEBHOOK_URL': 'general-secret'}, clear=True):
            with self.assertRaisesRegex(ValueError, 'DISCORD_WEBHOOK_PIXINSIGHT'):
                discord.send('pixinsight', '001')
        self.assertEqual(discord.destination('nina'), 'DISCORD_WEBHOOK_NINA')

    def test_discord_url_length_checked_after_expansion(self):
        path = self.root / 'content/specialists/digests/pixinsight/001.md'
        path.parent.mkdir(parents=True)
        path.write_text('🌌' * 1000 + '[URL]')
        with patch.object(discord, 'ROOT', self.root), patch.dict(os.environ, {'DISCORD_WEBHOOK_PIXINSIGHT': 'configured'}):
            with self.assertRaisesRegex(ValueError, 'UTF-16'):
                discord.send('pixinsight', '001')

    def test_forum_rejection_creates_one_thread_without_retrying_other_errors(self):
        webhook = 'https://discord.com/api/webhooks/123/test-token'
        error = urllib.error.HTTPError(webhook, 400, 'Bad request', {}, io.BytesIO(b'{"code":220001}'))
        from unittest.mock import MagicMock
        response = MagicMock()
        response.__enter__.return_value = io.BytesIO(b'{"id":"message","channel_id":"thread"}')
        with patch.object(discord.urllib.request, 'urlopen', side_effect=[error, response]) as request:
            result = discord.post_message(webhook, 'An edition', thread_name='PixInsight #001')
        self.assertEqual(result['channel_id'], 'thread')
        first = json.loads(request.call_args_list[0].args[0].data)
        second = json.loads(request.call_args_list[1].args[0].data)
        self.assertNotIn('thread_name', first)
        self.assertEqual(second['thread_name'], 'PixInsight #001')
        for failure in [urllib.error.HTTPError(webhook, 400, 'Bad request', {}, io.BytesIO(b'{"code":50035}')), OSError('timeout')]:
            with patch.object(discord.urllib.request, 'urlopen', side_effect=failure) as request:
                with self.assertRaises(RuntimeError):
                    discord.post_message(webhook, 'An edition')
                self.assertEqual(request.call_count, 1)

    def test_uncertain_delivery_is_not_reserved_again(self):
        box = self.root / 'data/discord-outbox.json'
        box.write_text(json.dumps({'messages': [
            {'series': 'pixinsight', 'slug': '001', 'status': 'uncertain'},
            {'series': 'nina', 'slug': '001', 'status': 'sending'},
            {'series': 'siril', 'slug': '001', 'status': 'pending'},
        ]}))
        batch = self.root / 'batch.json'
        with patch.object(discord_outbox, 'OUTBOX', box), patch.object(sys, 'argv', ['discord_outbox.py', 'reserve']), patch.dict(os.environ, {'BATCH_FILE': str(batch), 'DISCORD_WEBHOOK_SIRIL': 'configured'}):
            discord_outbox.main()
        self.assertEqual(json.loads(batch.read_text()), [{'series': 'siril', 'slug': '001'}])


if __name__ == '__main__':
    unittest.main()
