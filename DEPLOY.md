# Deploying YTRecap

## Today: Google Cloud project `yt-recap-376803` (YT-Recap)

The console dashboard for that project shows App Engine traffic and about $2/month in
charges. ytrecap.org points at Google's hosting addresses (216.239.3x.21 /
2001:4860:4802:3x::15), which is how App Engine custom domains work.

The same project also owns two things to keep:

- **The domain itself.** ytrecap.org was bought through **Google Cloud Domains** (Squarespace
  is the registrar of record, with Google Cloud Domains as the reseller). Its DNS is most
  likely a **Cloud DNS** zone in this project. The yearly renewal (every March) bills to
  this project's billing account.
- **The YouTube Data API key** (`YT_KEY`), which is free to use.

**Do not shut down this project** unless you've transferred the domain out first.

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
   `www.ytrecap.org`. Vercel offers the "Vercel nameservers" option
   (`ns1.vercel-dns.com`, `ns2.vercel-dns.com`); use that.
5. **Hand DNS to Vercel.** The domain's DNS currently runs on the retired Google Domains DNS
   (the console warns "Google Domains DNS settings that are no longer supported"), so it
   has to move anyway. In Google Cloud console, open **Cloud Domains → ytrecap.org → DNS
   details**:
   - If **DNSSEC** is on, turn it off first and wait for it to clear (up to 24–48 hours).
     Switching nameservers while DNSSEC is on can take the domain offline.
   - Note any MX (email) or other records you still need. You'd recreate those in Vercel.
   - Choose **custom name servers** and enter `ns1.vercel-dns.com` and
     `ns2.vercel-dns.com`.

   Vercel verifies the domain, creates the records for the site and issues HTTPS. This
   usually takes minutes, occasionally a few hours.
6. **Turn off Google hosting** once ytrecap.org shows the new site:
   - App Engine → Settings → **Disable application** (this stops serving and instance
     charges)
   - Cloud Storage → delete the `*.appspot.com` / `staging.*` buckets, and delete old images
     under Artifact Registry / Container Registry (this stops the storage charges)
   - Keep the project itself, because it holds the domain and `YT_KEY`.
   - Check Billing a few days later. The only remaining charge should be the yearly
     domain renewal each March.
7. **Optional: move the domain to Vercel too.** In Cloud Domains, unlock ytrecap.org and get
   its transfer (auth) code, then transfer it in on Vercel (Domains → Transfer In; this
   includes a paid year of renewal). After that, the Google project can be shut down
   entirely.

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

## Captions through a residential proxy

Set `YT_PROXY_URL` to the provider-supplied authenticated HTTP(S) proxy URL in
Vercel's **Preview** and **Production** environments, then deploy a new Preview.
Never commit the value or include it in logs. Caption traffic alone uses the proxy;
metadata and AI calls do not. With the variable absent, captions are fetched directly.

The caption client uses `youtube-transcript-api`'s `GenericProxyConfig` for both
HTTP and HTTPS. It attempts at most twice, with 3-second connect and 5-second read
inactivity timeouts within an 18-second shared request budget. Requests timeouts
are not a hard wall-clock limit against a continuously trickling response.
Successful timestamped captions are cached per worker for one hour (128 entries);
failed or empty results are never cached. Cold starts and other workers fetch again.

If captions remain unavailable, the result is visibly labeled a description-only
overview and has no requested chapters. These overviews are not summary-cached,
so subsequent attempts can recover captions. Automatic Gemini video watching has
been removed because it can exceed the hosting request window.

Before production, verify nonempty caption-based results on a short video and a
video longer than ten minutes in Preview. A successful description-only overview
is not evidence that the proxy works. Production must wait for Preview review.

Run regression tests from the repository root with:
`python -m unittest discover -s tests -v`.
