import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import app

class SummaryTests(unittest.TestCase):
    def setUp(self):
        app._cache.clear()
        self.video = dict(id='abcdefghijk', title='Title', channel='Channel', description='Description')
        self.client = Mock()
        self.client.chat.completions.create.side_effect = lambda **kw: iter([SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content='Summary'))])])

    def run_summary(self, transcript):
        with patch.object(app, 'DEMO_MODE', False), patch.object(app, 'fetch_video_info', return_value=self.video), patch.object(app, 'fetch_transcript', return_value=transcript), patch.object(app, 'PROVIDERS', [('test', self.client, 'test')]):
            return [json.loads(line) for line in app.summarize_stream('abcdefghijk', 'brief')]

    def test_description_is_labeled_and_not_cached(self):
        events = self.run_summary((None, False))
        self.assertEqual(next(e for e in events if e['type']=='video')['source'], 'description')
        prompt = self.client.chat.completions.create.call_args.kwargs['messages'][1]['content']
        self.assertIn('description-only overview', prompt)
        self.assertNotIn('## Chapters', prompt)
        self.assertEqual(events[-1]['type'], 'done')
        self.assertFalse(app._cache)
        self.run_summary(('[00:00] Actual caption', False))
        self.assertEqual(self.client.chat.completions.create.call_count, 2)

    def test_caption_summary_cache_preserves_source(self):
        first = self.run_summary(('[00:00] Actual caption', False))
        second = self.run_summary((None, False))
        self.assertEqual(next(e for e in second if e['type']=='video')['source'], 'transcript')
        self.assertEqual(self.client.chat.completions.create.call_count, 1)
        self.assertEqual(first[-1]['type'], 'done')

    def test_provider_failure_is_not_cached(self):
        self.client.chat.completions.create.side_effect = RuntimeError('failed')
        events = self.run_summary(('[00:00] Actual caption', False))
        self.assertEqual(events[-1]['type'], 'error')
        self.assertFalse(app._cache)

if __name__ == '__main__':
    unittest.main()
