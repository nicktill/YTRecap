# Deploying YTRecap

## Today: Google Cloud project `yt-recap-376803` (YT-Recap)

The console dashboard for that project shows App Engine traffic and about $2/month in
charges. ytrecap.org points at Google's hosting addresses (216.239.3x.21 /
2001:4860:4802:3x::15), which is how App Engine custom domains work. The same project most
likely also holds the **YouTube Data API key** (`YT_KEY`). That key is free to use, so it's
worth keeping.

## Moving everything to Vercel (free)

The Vercel project `ytrecap` (team *nicktill's projects*) is already created and linked to
this repo, with Root Directory `src`.

1. **Add secrets in Vercel.** Go to ytrecap → Settings → Environment Variables and add
   `OPENAI_KEY` (or `GEMINI_API_KEY`) plus `YT_KEY` (copy it from Google Cloud → APIs &
   Services → Credentials). Then redeploy.
2. **Ship the code.** Merge `redesign` into `main`. From then on, every push to `main`
   deploys to production automatically.
3. **Try it** at `ytrecap-nicktills-projects.vercel.app`.
4. **Attach the domain.** Go to ytrecap → Settings → Domains and add `ytrecap.org` and
   `www.ytrecap.org`. Vercel shows the exact DNS records it wants.
5. **Point DNS at Vercel.** At the registrar (wherever ytrecap.org is registered; if it was
   bought through Google Domains, it now lives at Squarespace Domains):
   - delete the old Google **A** records (216.239.32.21, .34.21, .36.21, .38.21)
   - delete the old Google **AAAA** records (2001:4860:4802:32/34/36/38::15). Leftover AAAA
     records keep sending IPv6 visitors to Google.
   - add the records Vercel showed you, typically an A record `@ → 76.76.21.21` and a
     CNAME `www → cname.vercel-dns.com`

   Vercel issues HTTPS automatically once DNS resolves, usually within minutes (up to a
   few hours).
6. **Turn off Google hosting** once ytrecap.org shows the new site:
   - App Engine → Settings → **Disable application** (this stops serving and instance
     charges)
   - Cloud Storage → delete the `*.appspot.com` / `staging.*` buckets, and delete old images
     under Artifact Registry / Container Registry (this stops the storage charges)
   - Keep the project itself if `YT_KEY` lives there. Otherwise **IAM & Admin → Settings →
     Shut down** removes everything (recoverable for 30 days).
   - Check Billing a few days later to confirm charges have stopped.

## Option B: stay on Cloud Run (without Zeet)

The Procfile makes this a single command from `src/`:

```bash
gcloud run deploy <existing-service-name> --source . --region <region> \
  --allow-unauthenticated --min-instances 0 \
  --set-env-vars GEMINI_API_KEY=...,YT_KEY=...
```

Reusing the existing service name keeps the ytrecap.org domain mapping. Afterwards, set
an Artifact Registry cleanup policy so old images get deleted automatically.

## AI costs

The original site called the **OpenAI API** (`gpt-3.5-turbo`) with whatever key was set as
`OPENAI_KEY` in the host's environment variables. That key is billed to the OpenAI account
that created it; check [platform.openai.com/usage](https://platform.openai.com/usage) and
the API keys page there.

The app now prefers a **free Gemini key** (`GEMINI_API_KEY` from
[aistudio.google.com/apikey](https://aistudio.google.com/apikey)) and uses the
`gemini-flash-latest` model by default. The free tier is rate-limited (on the order of 10–15
requests a minute), and Google may use free-tier requests to improve its products. If the
limit is hit, users see a friendly "try again in a minute" message. `OPENAI_KEY` still works
if you'd rather pay, and `AI_MODEL` overrides the model for either provider.

## Known limitation: transcripts from cloud servers

YouTube often blocks transcript requests that come from datacenter IPs (Vercel, GCP, AWS).
When that happens, the app falls back to summarizing from the title and description, and
the UI labels it "From description". Getting transcripts reliably in production needs a
residential proxy, which `youtube-transcript-api` supports but which costs money.
