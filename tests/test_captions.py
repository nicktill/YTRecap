import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import captions
import requests
from youtube_transcript_api import NoTranscriptFound, RequestBlocked, TranscriptsDisabled


def snippet(text="spoken words", start=0):
    return SimpleNamespace(text=text, start=start)


class CaptionTests(unittest.TestCase):
    def setUp(self):
        self.cache = captions.CaptionCache()
        self.api = MagicMock()
        self.track = self.api.list.return_value.find_transcript.return_value
        self.track.fetch.return_value = [snippet()]
        self.factory = MagicMock(return_value=self.api)

    def fetch(self, **kwargs):
        return captions.fetch_transcript("abcdefghijk", api_factory=self.factory, cache=self.cache, **kwargs)

    def test_proxy_applies_to_both_schemes_and_success_is_cached(self):
        with patch.dict(os.environ, {"YT_PROXY_URL": "http://test-user:test-password@proxy.invalid:823"}):
            self.assertEqual(self.fetch(), ("[00:00] spoken words", False))
            self.assertEqual(self.fetch(), ("[00:00] spoken words", False))
        self.factory.assert_called_once()
        args = self.factory.call_args.kwargs
        self.assertEqual(args["proxy_config"].to_requests_dict(), {
            "http": "http://test-user:test-password@proxy.invalid:823",
            "https": "http://test-user:test-password@proxy.invalid:823",
        })
        self.assertFalse(args["http_client"].trust_env)

    def test_non_english_uses_same_listing(self):
        available = self.api.list.return_value
        available.find_transcript.side_effect = NoTranscriptFound("abcdefghijk", ["en"], available)
        available.__iter__.return_value = iter([self.track])
        self.assertEqual(self.fetch()[0], "[00:00] spoken words")
        self.api.list.assert_called_once()

    def test_block_is_retried_bounded_and_not_cached(self):
        self.api.list.side_effect = RequestBlocked("abcdefghijk")
        self.assertEqual(self.fetch(), (None, False))
        self.assertEqual(self.factory.call_count, 2)
        self.api.list.side_effect = None
        self.assertIsNotNone(self.fetch()[0])

    def test_captionless_and_empty_not_cached(self):
        self.api.list.side_effect = TranscriptsDisabled("abcdefghijk")
        self.assertEqual(self.fetch(), (None, True))
        self.assertEqual(self.factory.call_count, 1)
        self.api.list.side_effect = None
        self.track.fetch.return_value = [snippet("[Music]")]
        self.assertEqual(self.fetch(), (None, True))
        self.track.fetch.return_value = [snippet()]
        self.assertIsNotNone(self.fetch()[0])

    def test_exception_secret_never_logged(self):
        self.api.list.side_effect = requests.ConnectionError("http://secret:password@proxy.invalid")
        with self.assertLogs("captions", level="WARNING") as logs:
            self.assertEqual(self.fetch(), (None, False))
        self.assertNotIn("secret", str(logs.output))
        self.assertNotIn("password", str(logs.output))

    def test_deadline_stops_retry(self):
        now = [0]
        def fail(*args):
            now[0] = 19
            raise requests.Timeout("slow")
        self.api.list.side_effect = fail
        self.assertEqual(self.fetch(clock=lambda: now[0]), (None, False))
        self.factory.assert_called_once()

    def test_session_timeout_and_expired_deadline(self):
        now = [10]
        session = captions.DeadlineSession(12, clock=lambda: now[0])
        request = requests.Request("GET", "https://example.invalid").prepare()
        with patch.object(requests.Session, "send", return_value=MagicMock()) as send:
            session.send(request)
            timeout = send.call_args.kwargs["timeout"]
            self.assertEqual(timeout.total, 2)
            self.assertEqual(timeout.connect_timeout, 2)
            now[0] = 12
            with self.assertRaises(requests.Timeout):
                session.send(request)
            send.assert_called_once()
        session.close()

    def test_ttl_and_lru_bound(self):
        now = [0]
        cache = captions.CaptionCache(max_entries=2, ttl=10, clock=lambda: now[0])
        cache.put("a", "A")
        cache.put("b", "B")
        self.assertEqual(cache.get("a"), "A")
        cache.put("c", "C")
        self.assertIsNone(cache.get("b"))
        now[0] = 10
        self.assertIsNone(cache.get("a"))
        cache.put("empty", None)
        self.assertNotIn("empty", cache.entries)

    def test_timestamp_grouping_long_video_and_character_cap(self):
        self.assertEqual(captions.format_captions([
            snippet("[Music] hello\nworld", 2), snippet("next", 32), snippet("later", 3671)
        ]), "[00:02] hello world next\n[1:01:11] later")
        text = captions.format_captions([snippet("x" * 200, i * 31) for i in range(2000)])
        self.assertLessEqual(len(text), captions.MAX_TRANSCRIPT_CHARS)
        self.assertIn("[17:", text)


if __name__ == "__main__":
    unittest.main()
