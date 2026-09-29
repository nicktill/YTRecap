# YTRecap

[YTRecap](https://ytrecap.org) turns YouTube captions into AI summaries, key takeaways, and clickable chapters. The Flask app streams results as they are generated and supports brief, standard, and detailed summaries, light/dark themes, and Markdown downloads.

Captions are fetched with `youtube-transcript-api`, optionally through a residential proxy configured with `YT_PROXY_URL`. The YouTube Data API supplies metadata when `YT_KEY` is configured; otherwise, the app uses oEmbed for the title and channel. An OpenAI-compatible provider is tried first, with Gemini as a backup, each with short timeouts.

When captions cannot be retrieved, a **description-only** result is visibly labeled and has no generated timestamp chapters. If there is no usable description either, the app reports that it cannot summarize the video. Demo mode shows a clearly labeled sample rather than fetching captions or calling an AI provider.

## Preview

Landing page (dark mode):

![YTRecap landing page in dark mode: Watch less. Understand more.](docs/images/landing.jpg)

A summary with key takeaways (these screenshots use the built-in sample, labeled "Example summary"):

![YTRecap summary view in light mode](docs/images/result-light.jpg)

![YTRecap summary view in dark mode](docs/images/result-dark.jpg)

## Run locally

```bash
git clone https://github.com/nicktill/YTRecap.git
cd YTRecap
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
cp src/.env.example src/.env
# Edit src/.env to add GEMINI_API_KEY or OPENAI_KEY.
cd src
python app.py
```

Open [localhost:5050](http://localhost:5050). Without an AI key, the app runs in demo mode and streams a sample summary. Set `YTRECAP_DEMO=1` to force demo mode even when keys are configured.

Optional settings in `src/.env`:

- `YT_PROXY_URL`: authenticated HTTP(S) residential proxy URL used only for captions. Keep the value private and out of Git.
- `YT_KEY`: YouTube Data API key for descriptions, duration, views, and publication dates.
- `GEMINI_MODEL`, `OPENAI_MODEL`, `OPENAI_BASE_URL`: provider overrides.

Share links work by swapping the domain: `ytrecap.org/watch?v=VIDEO_ID`.

## Caption behavior and tests

Caption retrieval has at most two attempts, bounded request timeouts, and a shared request deadline. Successful timestamped captions are cached for one hour in a bounded cache within each worker; errors and missing captions are not cached. A configured proxy is not a guarantee that YouTube will serve captions—verify actual short and long videos on a deployed Preview before promoting it.

Run the regression suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

For Vercel, use `src` as the project's Root Directory and configure secrets separately for Preview and Production. See [DEPLOY.md](DEPLOY.md) for deployment notes.

[MIT license](LICENSE)
