"""YTRecap: AI summaries for any YouTube video."""
import json
import os
import re
import time
from collections import OrderedDict

import isodate
import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, stream_with_context
from openai import OpenAI, RateLimitError
from captions import fetch_transcript


load_dotenv()

app = Flask(__name__)

# AI providers, tried in order: Gemini (free key from aistudio.google.com) first,
# then any OpenAI-compatible key (OPENAI_BASE_URL can point it elsewhere).
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
OPENAI_KEY = os.environ.get("OPENAI_KEY") or os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
YT_KEY = os.environ.get("YT_KEY")

PROVIDERS = []  # (name, client, model)
if GEMINI_KEY:
    PROVIDERS.append(("gemini", OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/", max_retries=1), GEMINI_MODEL))
if OPENAI_KEY:
    PROVIDERS.append(("openai", OpenAI(api_key=OPENAI_KEY, base_url=os.environ.get("OPENAI_BASE_URL")), OPENAI_MODEL))
AI_MODEL = " -> ".join(m for _, _, m in PROVIDERS)
# Demo mode streams a canned summary so the UI can be previewed without API keys.
DEMO_MODE = os.environ.get("YTRECAP_DEMO") == "1" or not PROVIDERS

LENGTHS = {
    "brief": {"words": 150, "takeaways": "3", "chapters": "3-5"},
    "standard": {"words": 350, "takeaways": "4-6", "chapters": "4-8"},
    "detailed": {"words": 750, "takeaways": "6-8", "chapters": "6-12"},
}

VIDEO_ID_PATTERNS = [
    r"(?:v=|vi=)([\w-]{11})",
    r"youtu\.be/([\w-]{11})",
    r"/(?:shorts|embed|live|v)/([\w-]{11})",
    r"^/?([\w-]{11})$",
]


def extract_video_id(text):
    text = (text or "").strip()
    for pattern in VIDEO_ID_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_duration(iso):
    total = int(isodate.parse_duration(iso).total_seconds())
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_count(n):
    n = int(n)
    for threshold, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if n >= threshold:
            value = n / threshold
            return f"{value:.1f}".rstrip("0").rstrip(".") + suffix
    return str(n)


def format_date(iso):
    return time.strftime("%b %-d, %Y", time.strptime(iso[:10], "%Y-%m-%d"))


def format_timestamp(seconds):
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


# ---------------------------------------------------------------------------
# YouTube data
# ---------------------------------------------------------------------------

class VideoNotFound(Exception):
    pass


def fetch_video_info(video_id):
    """Video metadata from the Data API, or oEmbed when no API key is configured."""
    if YT_KEY:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "snippet,statistics,contentDetails", "id": video_id, "key": YT_KEY},
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            raise VideoNotFound
        item = items[0]
        snippet, stats = item["snippet"], item.get("statistics", {})
        return {
            "id": video_id,
            "title": snippet["title"],
            "channel": snippet["channelTitle"],
            "description": snippet.get("description", ""),
            "published": format_date(snippet["publishedAt"]),
            "views": format_count(stats["viewCount"]) if "viewCount" in stats else None,
            "duration": format_duration(item["contentDetails"]["duration"]),
        }

    resp = requests.get(
        "https://www.youtube.com/oembed",
        params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
        timeout=10,
    )
    if resp.status_code in (400, 401, 403, 404):
        raise VideoNotFound
    resp.raise_for_status()
    data = resp.json()
    return {
        "id": video_id,
        "title": data.get("title", "Untitled video"),
        "channel": data.get("author_name", ""),
        "description": "",
        "published": None,
        "views": None,
        "duration": None,
    }


# ---------------------------------------------------------------------------
# Summarization
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are YTRecap, an expert at distilling YouTube videos into clear, \
skimmable summaries. Write in confident, plain English. Never mention "the transcript" \
or "the captions"; speak about the video directly. Output GitHub-flavored Markdown only, \
using exactly the sections you are asked for, in order, with `## ` headings."""


def build_prompt(video, transcript, length, source=None):
    spec = LENGTHS[length]
    header = (
        f"Title: {video['title']}\nChannel: {video['channel']}\n"
        f"Description:\n{video['description'][:3000] or '(none)'}\n"
    )
    sections = f"""## TL;DR
One or two sentences capturing the core point of the video.

## Key takeaways
{spec['takeaways']} bullets. Start each with a short **bold lead-in** followed by one sentence.

## Summary
About {spec['words']} words of well-structured prose in short paragraphs."""

    if transcript:
        sections += f"""

## Chapters
{spec['chapters']} bullets, each formatted exactly as `- [mm:ss] Chapter title — one-line description`.
Only use timestamps that appear in the transcript below."""
        return f"{header}\nTimestamped transcript:\n{transcript}\n\nWrite these sections:\n\n{sections}"

    return (
        f"{header}\nNo transcript is available, so base the summary on the title, channel and "
        f"description. Explicitly say this is a description-only overview, not a summary of the full video. Do not invent specifics, chapters, or timestamps.\n\n"
        f"Write these sections:\n\n{sections}"
    )


# Small in-process cache so re-requesting a summary doesn't re-bill the API.
_cache = OrderedDict()
CACHE_SIZE = 200


def cache_get(key):
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]
    return None


def cache_put(key, value):
    _cache[key] = value
    _cache.move_to_end(key)
    while len(_cache) > CACHE_SIZE:
        _cache.popitem(last=False)


def event(kind, **data):
    return json.dumps({"type": kind, **data}) + "\n"


def summarize_stream(video_id, length, fresh=False):
    if DEMO_MODE:
        yield from demo_stream(length)
        return

    yield event("status", step="video")
    try:
        video = fetch_video_info(video_id)
    except VideoNotFound:
        yield event("error", message="We couldn't find that video. It may be private or removed.")
        return
    except requests.RequestException:
        app.logger.exception("YouTube metadata request failed")
        yield event("error", message="YouTube didn't respond. Please try again in a moment.")
        return

    yield event("status", step="transcript")
    cached = None if fresh else cache_get((video_id, length))
    transcript, _captionless = (None, True) if cached else fetch_transcript(video_id)
    if cached:
        source = cached["source"]
    elif transcript:
        source = "transcript"
    else:
        source = "description"
    if source == "description" and not video.get("description", "").strip():
        yield event("error", message="Captions are unavailable and this video has no usable description. Please try again later.")
        return
    video_public = {k: v for k, v in video.items() if k != "description"}
    yield event("video", video=video_public, source=source)

    if cached:
        yield event("delta", text=cached["text"])
        yield event("done")
        return

    yield event("status", step="writing")
    parts = []
    prompt = build_prompt(video, transcript, length)
    for i, (name, client, model) in enumerate(PROVIDERS):
        try:
            stream = client.chat.completions.create(
                model=model,
                temperature=0.4,
                stream=True,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    parts.append(chunk.choices[0].delta.content)
                    yield event("delta", text=chunk.choices[0].delta.content)
            break
        except Exception as exc:
            app.logger.warning("%s summary failed: %s", name, " ".join(str(exc).split())[:300])
            # Fall through to the next provider only if nothing was streamed yet.
            if parts or i == len(PROVIDERS) - 1:
                if isinstance(exc, RateLimitError):
                    yield event("error", message="YTRecap is a bit busy right now. Please try again in a minute.")
                else:
                    yield event("error", message="Something went wrong while writing the summary. Please try again.")
                return

    if source == "transcript" and parts:
        cache_put((video_id, length), {"text": "".join(parts), "source": source})
    yield event("done")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/healthz")
def healthz():
    return jsonify(ok=True)


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    payload = request.get_json(silent=True) or {}
    video_id = extract_video_id(payload.get("url", ""))
    length = payload.get("length", "standard")
    if not video_id:
        return jsonify(error="That doesn't look like a YouTube link. Try pasting the full video URL."), 400
    if length not in LENGTHS:
        length = "standard"
    return Response(
        stream_with_context(summarize_stream(video_id, length, bool(payload.get("fresh")))),
        mimetype="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/robots.txt")
def robots():
    body = "User-agent: *\nAllow: /\n\nSitemap: https://ytrecap.org/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url><loc>https://ytrecap.org/</loc></url>\n"
        "</urlset>\n"
    )
    return Response(body, mimetype="application/xml")


# Catch-all so youtube.com links work with the domain swapped in, e.g.
# ytrecap.org/watch?v=ID, ytrecap.org/shorts/ID or ytrecap.org/ID.
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def index(path):
    initial_id = request.args.get("v") or extract_video_id("/" + path)
    return render_template("index.html", initial_id=initial_id or "", demo=DEMO_MODE)


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

DEMO_VIDEO = {
    "id": "UF8uR6Z6KLc",
    "title": "Steve Jobs' 2005 Stanford Commencement Address",
    "channel": "Stanford",
    "published": "Mar 7, 2008",
    "views": "44M",
    "duration": "15:05",
}

DEMO_SUMMARY = """## TL;DR
Steve Jobs tells three stories from his life — about connecting the dots, love and loss, and death — to argue that you should trust your intuition, do work you love, and not waste your limited time living someone else's life.

## Key takeaways
- **Trust the dots will connect.** You can't plan your path looking forward; meaning only becomes clear in hindsight, so trust your curiosity.
- **Setbacks can be gifts.** Being fired from Apple freed Jobs to be a beginner again and led to NeXT, Pixar, and his family.
- **Do what you love.** Great work comes from loving what you do; if you haven't found it yet, keep looking and don't settle.
- **Let mortality focus you.** Remembering that you will die is the best tool for cutting through fear, pride, and other people's expectations.
- **Stay hungry, stay foolish.** Keep a beginner's hunger and willingness to take risks throughout your life.

## Summary
Jobs opens by admitting he never graduated from college, then offers three stories instead of a traditional speech.

The first is about connecting the dots. He dropped out of Reed College after six months to stop spending his working-class parents' savings, then stayed on to drop in on classes that interested him. A calligraphy course seemed useless at the time, yet ten years later it shaped the Macintosh's beautiful typography. His point: you can only connect the dots looking backward, so you have to trust that they will connect.

The second story is about love and loss. Jobs started Apple in his parents' garage at 20, and by 30 he was publicly fired from the company he founded. Though devastating, it turned out to be one of the best things that ever happened to him. The heaviness of success was replaced by the lightness of being a beginner, and in the following years he started NeXT, built Pixar, and met his wife. Apple later bought NeXT and he returned. He urges graduates to find work they love, because it is the only way to do great work.

The third story is about death. Diagnosed with pancreatic cancer a year earlier, Jobs describes facing mortality up close. Remembering that you are going to die, he says, is the best way to avoid the trap of thinking you have something to lose. Your time is limited, so don't let the noise of others' opinions drown out your inner voice.

He closes with the farewell message from the final issue of the Whole Earth Catalog: "Stay hungry. Stay foolish."

## Chapters
- [00:00] Introduction — Jobs admits this is the closest he's come to a college graduation.
- [00:55] Connecting the dots — Dropping out of Reed, and how a calligraphy class shaped the Mac.
- [05:05] Love and loss — Starting Apple, getting fired, and the creative rebirth that followed.
- [09:05] Death — His cancer diagnosis and using mortality to focus on what matters.
- [13:35] Stay hungry, stay foolish — The Whole Earth Catalog and his parting wish for graduates.
"""


def demo_stream(length):  # noqa: ARG001 - the sample is the same at every length
    for step in ("video", "transcript"):
        yield event("status", step=step)
        time.sleep(0.5)
    yield event("video", video=DEMO_VIDEO, source="transcript", demo=True)
    yield event("status", step="writing")
    time.sleep(0.6)
    for token in re.findall(r"\S+\s*", DEMO_SUMMARY):
        yield event("delta", text=token)
        time.sleep(0.012)
    yield event("done")


if __name__ == "__main__":
    mode = "demo mode (no AI key set)" if DEMO_MODE else f"model {AI_MODEL}"
    print(f"YTRecap running on http://localhost:{os.environ.get('PORT', 5050)} using {mode}")
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5050)))
