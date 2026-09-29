"""Bounded caption retrieval through the optional residential proxy.

Cache entries are successful timestamped captions only, local to each worker.
"""
import logging
import os
import re
import threading
import time
from collections import OrderedDict

import requests
from urllib3.util import Timeout
from youtube_transcript_api import (
    NoTranscriptFound, RequestBlocked, TranscriptsDisabled, VideoUnavailable,
    YouTubeTranscriptApi,
)
from youtube_transcript_api.proxies import GenericProxyConfig

LOGGER = logging.getLogger(__name__)
MAX_TRANSCRIPT_CHARS = 120_000
FETCH_BUDGET_SECONDS = 18
MAX_ATTEMPTS = 2
CACHE_TTL_SECONDS = 3600
CACHE_MAX_ENTRIES = 128


class DeadlineSession(requests.Session):
    """Cap every library request; never start another after the shared deadline.

    Requests timeouts bound connect/read inactivity, not wall time for a server
    continually trickling bytes. The deadline also stops redirects and retries.
    """
    def __init__(self, deadline, clock=time.monotonic):
        super().__init__()
        self.deadline = deadline
        self.clock = clock
        self.trust_env = False
        self.max_redirects = 3

    def send(self, request, **kwargs):
        remaining = self.deadline - self.clock()
        if remaining <= 0:
            raise requests.Timeout("Caption request budget exhausted")
        kwargs["timeout"] = Timeout(total=remaining, connect=min(3, remaining), read=min(5, remaining))
        return super().send(request, **kwargs)


class CaptionCache:
    def __init__(self, max_entries=CACHE_MAX_ENTRIES, ttl=CACHE_TTL_SECONDS, clock=time.monotonic):
        self.entries = OrderedDict()
        self.lock = threading.Lock()
        self.max_entries, self.ttl, self.clock = max_entries, ttl, clock

    def get(self, key):
        with self.lock:
            entry = self.entries.get(key)
            if entry is None:
                return None
            expires, value = entry
            if expires <= self.clock():
                del self.entries[key]
                return None
            self.entries.move_to_end(key)
            return value

    def put(self, key, value):
        if not value:
            return
        with self.lock:
            self.entries[key] = (self.clock() + self.ttl, value)
            self.entries.move_to_end(key)
            while len(self.entries) > self.max_entries:
                self.entries.popitem(last=False)


_CACHE = CaptionCache()


def _timestamp(seconds):
    hours, rem = divmod(int(seconds), 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def format_captions(snippets):
    blocks, current, block_start = [], [], None
    for snippet in snippets:
        text = re.sub(r"\[[^\]]*\]", "", snippet.text).replace("\n", " ").strip()
        if not text:
            continue
        if block_start is None:
            block_start = snippet.start
        current.append(text)
        if snippet.start - block_start >= 30:
            blocks.append(f"[{_timestamp(block_start)}] {' '.join(current)}")
            current, block_start = [], None
    if current:
        blocks.append(f"[{_timestamp(block_start)}] {' '.join(current)}")
    # Sample the whole video, preserving source timestamps, then enforce the cap.
    total = sum(len(block) + 1 for block in blocks)
    if total > MAX_TRANSCRIPT_CHARS:
        count = max(1, int(len(blocks) * MAX_TRANSCRIPT_CHARS / total))
        indexes = [round(i * (len(blocks) - 1) / max(1, count - 1)) for i in range(count)]
        blocks = [blocks[i] for i in indexes]
    return "\n".join(blocks)[:MAX_TRANSCRIPT_CHARS] or None


def fetch_transcript(video_id, *, api_factory=YouTubeTranscriptApi,
                     session_factory=DeadlineSession, cache=_CACHE, clock=time.monotonic):
    """Return (timestamped text, captionless); failures are never cached.

    A block, timeout, malformed response, or unavailable video is not evidence
    that a video has no captions. Logs deliberately omit exception text/URLs.
    """
    cached = cache.get(video_id)
    if cached is not None:
        return cached, False
    deadline = clock() + FETCH_BUDGET_SECONDS
    proxy_url = os.environ.get("YT_PROXY_URL", "").strip()
    proxy = GenericProxyConfig(http_url=proxy_url, https_url=proxy_url) if proxy_url else None
    for attempt in range(MAX_ATTEMPTS):
        if clock() >= deadline:
            break
        try:
            with session_factory(deadline, clock=clock) as session:
                api = api_factory(proxy_config=proxy, http_client=session)
                # List once so a non-English fallback doesn't repeat discovery.
                available = api.list(video_id)
                try:
                    transcript = available.find_transcript(["en", "en-US", "en-GB"])
                except NoTranscriptFound:
                    transcript = next(iter(available))
                text = format_captions(transcript.fetch())
                if text:
                    cache.put(video_id, text)
                    return text, False
                return None, True
        except (TranscriptsDisabled, NoTranscriptFound, StopIteration):
            return None, True
        except (RequestBlocked, requests.RequestException) as exc:
            LOGGER.warning("Caption attempt %d failed (%s)", attempt + 1, type(exc).__name__)
        except Exception as exc:
            LOGGER.warning("Caption retrieval failed (%s)", type(exc).__name__)
            return None, False
    return None, False
