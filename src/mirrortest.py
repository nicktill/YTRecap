"""Temporary: can public Invidious / Piped mirrors return captions from Vercel?"""
import time
import requests

UA = {"User-Agent": "Mozilla/5.0 YTRecap caption test"}


def timed(fn):
    t = time.time()
    try:
        out = fn()
    except Exception as exc:
        out = {"error": f"{type(exc).__name__}: {str(exc)[:120]}"}
    out["secs"] = round(time.time() - t, 1)
    return out


def invidious(host, vid):
    r = requests.get(f"{host}/api/v1/captions/{vid}", headers=UA, timeout=8)
    out = {"status": r.status_code}
    caps = r.json().get("captions", []) if r.ok else []
    out["tracks"] = [c.get("languageCode") for c in caps][:5]
    if caps:
        t = requests.get(host + caps[0]["url"], headers=UA, timeout=8)
        out["track_status"], out["chars"], out["sample"] = t.status_code, len(t.text), t.text[:100]
    return out


def piped(host, vid):
    r = requests.get(f"{host}/streams/{vid}", headers=UA, timeout=8)
    out = {"status": r.status_code}
    subs = r.json().get("subtitles", []) if r.ok else []
    out["tracks"] = [s.get("code") for s in subs][:5]
    if subs:
        t = requests.get(subs[0]["url"], headers=UA, timeout=8)
        out["track_status"], out["chars"], out["sample"] = t.status_code, len(t.text), t.text[:100]
    return out


def run(vid):
    results = {}
    try:
        inst = requests.get("https://api.invidious.io/instances.json?sort_by=health", headers=UA, timeout=8).json()
        hosts = [d["uri"] for _, d in inst if d.get("api") and d.get("type") == "https"][:6]
    except Exception as exc:
        hosts, results["instances_error"] = [], str(exc)[:120]
    for h in hosts:
        results["inv " + h] = timed(lambda h=h: invidious(h, vid))
    for h in ["https://pipedapi.kavin.rocks", "https://pipedapi.adminforge.de", "https://api.piped.private.coffee"]:
        results["piped " + h] = timed(lambda h=h: piped(h, vid))
    return results
