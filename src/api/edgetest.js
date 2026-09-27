// Temporary: can Vercel's edge network fetch YouTube captions?
export const config = { runtime: "edge" };

export default async function handler(req) {
  const v = new URL(req.url).searchParams.get("v") || "W07V7ljVVjU";
  const out = {};
  try {
    const r = await fetch("https://www.youtube.com/youtubei/v1/player?prettyPrint=false", {
      method: "POST",
      headers: { "Content-Type": "application/json", "User-Agent": "com.google.android.youtube/20.10.38 (Linux; U; Android 11) gzip" },
      body: JSON.stringify({ context: { client: { clientName: "ANDROID", clientVersion: "20.10.38", androidSdkVersion: 30, hl: "en" } }, videoId: v }),
    });
    const d = await r.json();
    const tracks = d?.captions?.playerCaptionsTracklistRenderer?.captionTracks || [];
    out.playability = d?.playabilityStatus?.status + " " + (d?.playabilityStatus?.reason || "");
    out.tracks = tracks.length;
    if (tracks.length) {
      const t = await fetch(tracks[0].baseUrl + "&fmt=json3");
      out.trackStatus = t.status;
      out.trackBytes = (await t.text()).length;
    }
  } catch (e) { out.error = String(e); }
  return new Response(JSON.stringify(out), { headers: { "content-type": "application/json" } });
}
