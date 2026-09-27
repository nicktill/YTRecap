"""Temporary: compare caption-fetch methods from this server's IP."""
import json, re
import requests
from youtube_transcript_api import YouTubeTranscriptApi

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
CLIENTS = {
    "android": ({"clientName": "ANDROID", "clientVersion": "20.10.38", "androidSdkVersion": 30},
                "com.google.android.youtube/20.10.38 (Linux; U; Android 11) gzip"),
    "ios": ({"clientName": "IOS", "clientVersion": "20.10.4", "deviceModel": "iPhone16,2"},
            "com.google.ios.youtube/20.10.4 (iPhone16,2; U; CPU iOS 18_3 like Mac OS X)"),
    "web": ({"clientName": "WEB", "clientVersion": "2.20250925.01.00"}, UA),
    "tv": ({"clientName": "TVHTML5_SIMPLY_EMBEDDED_PLAYER", "clientVersion": "2.0"}, UA),
    "mweb": ({"clientName": "MWEB", "clientVersion": "2.20250925.01.00"}, UA),
}


def fetch_track(url):
    r = requests.get(url + "&fmt=json3", headers={"User-Agent": UA}, timeout=10)
    text = ""
    try:
        ev = r.json().get("events", [])
        text = " ".join("".join(s.get("utf8", "") for s in e.get("segs", [])) for e in ev)
    except Exception:
        pass
    return {"track_status": r.status_code, "chars": len(text), "sample": text[:80],
            "acao": r.headers.get("access-control-allow-origin")}


def innertube(vid, name):
    ctx, ua = CLIENTS[name]
    r = requests.post("https://www.youtube.com/youtubei/v1/player?prettyPrint=false",
                      json={"context": {"client": {**ctx, "hl": "en"}}, "videoId": vid},
                      headers={"User-Agent": ua, "Origin": "https://www.youtube.com"}, timeout=10)
    out = {"status": r.status_code, "acao": r.headers.get("access-control-allow-origin")}
    d = r.json() if r.ok else {}
    out["playability"] = d.get("playabilityStatus", {}).get("status"), d.get("playabilityStatus", {}).get("reason")
    tracks = d.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
    out["tracks"] = len(tracks)
    if tracks:
        out.update(fetch_track(tracks[0]["baseUrl"]))
    return out


def watchpage(vid):
    r = requests.get(f"https://www.youtube.com/watch?v={vid}", headers={"User-Agent": UA, "Accept-Language": "en"},
                     cookies={"CONSENT": "YES+"}, timeout=10)
    out = {"status": r.status_code, "bot_check": "confirm you" in r.text}
    m = re.search(r'"captionTracks":(\[.*?\])', r.text)
    if m:
        tracks = json.loads(m.group(1))
        out["tracks"] = len(tracks)
        out.update(fetch_track(tracks[0]["baseUrl"]))
    return out


def run(vid):
    results = {}
    def attempt(name, fn):
        try:
            results[name] = fn()
        except Exception as exc:
            results[name] = {"error": f"{type(exc).__name__}: {str(exc)[:160]}"}
    attempt("transcript_api", lambda: {"chars": len(" ".join(s.text for s in YouTubeTranscriptApi().fetch(vid)))})
    for c in CLIENTS:
        attempt("innertube_" + c, lambda c=c: innertube(vid, c))
    attempt("watch_page", lambda: watchpage(vid))
    return results
