# Deploying YTRecap

## How it's deployed today (as far as we can tell)

There is no deployment config in this repo's history (no Dockerfile, `app.yaml`, or
Procfile), so the setup lived outside the repo. The clues:

- `ytrecap.org` resolves to `2001:4860:4802:32/34/36/38::15`. Those are Google's
  `ghs.googlehosted.com` addresses, which Google uses for **Cloud Run domain mappings**
  (and App Engine / Firebase custom domains).
- `app.py` reads `$PORT`, which is the Cloud Run convention.
- Zeet worked by building your repo and deploying it into *your own* GCP project on
  Cloud Run.

So most likely: **Zeet built the app and deployed it to Cloud Run in your GCP project,
with ytrecap.org mapped to that service.** To confirm, open
[console.cloud.google.com/run](https://console.cloud.google.com/run) (or run
`gcloud run services list` and `gcloud beta run domain-mappings list --region <region>`).

### Where the ~$3/month probably comes from

Cloud Run's free tier (2M requests and 180k vCPU-seconds a month) almost certainly covers
the traffic. Check **Billing → Reports, grouped by SKU**. The usual suspects:

- **Artifact Registry / Container Registry storage**: every Zeet build pushed an image,
  and old images add up past the 0.5 GB free tier.
- **Cloud Build** minutes, or **a minimum instance** set above 0.
- If the charge is from Zeet itself or your domain registrar, it won't show up in GCP at all.

## Option A (recommended, free): Vercel Hobby

You already use Vercel for other projects. The Hobby plan is free for personal,
non-commercial projects and runs Flask natively (`src/vercel.json` sets a 60s max
duration for streaming).

1. Vercel → **Add New… → Project** → import `nicktill/YTRecap`.
2. Set **Root Directory** to `src`. The framework is detected as Flask from `app.py`.
3. Under **Environment Variables**, add `OPENAI_KEY` (and optionally `YT_KEY` and
   `OPENAI_MODEL`). Deploy, then test the `*.vercel.app` URL.
4. **Settings → Domains** → add `ytrecap.org` and `www.ytrecap.org`. Vercel shows the
   DNS records to set at your registrar; replace the old Google records with them.
5. Once the new site is live on the domain, shut down the old one in GCP: delete the Cloud
   Run service, its domain mapping, and the old images in Artifact/Container Registry.
   That's what stops the bill.

After that, every push to `main` redeploys automatically.

## Option B: stay on Cloud Run (without Zeet)

The Procfile makes this a single command from `src/`:

```bash
gcloud run deploy <existing-service-name> --source . --region <region> \
  --allow-unauthenticated --min-instances 0 \
  --set-env-vars OPENAI_KEY=...,YT_KEY=...
```

Reusing the existing service name keeps the ytrecap.org domain mapping. Afterwards, set
an Artifact Registry cleanup policy so old images get deleted automatically.

## AI costs

Summaries call the **OpenAI API** with the key in `OPENAI_KEY` (the old code used
`gpt-3.5-turbo`; now `gpt-4o-mini` by default, set with `OPENAI_MODEL`). It's pay-as-you-go
and billed to whichever OpenAI account owns that key. Check
[platform.openai.com/usage](https://platform.openai.com/usage). At low traffic, a summary
costs a fraction of a cent.

To make AI free too, point the app at Google Gemini's free tier through its
OpenAI-compatible endpoint. No code changes needed:

```
OPENAI_KEY=<Gemini API key from aistudio.google.com>
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=<a current Gemini Flash model name>
```

(The free tier is rate-limited, and Google may use free-tier data to improve its products.)

## Known limitation: transcripts from cloud servers

YouTube often blocks transcript requests that come from datacenter IPs (Vercel, GCP, AWS).
When that happens, the app falls back to summarizing from the title and description, and
the UI labels it "From description". Getting transcripts reliably in production needs a
residential proxy, which `youtube-transcript-api` supports but which costs money.
