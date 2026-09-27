# YTRecap [![GitHub stars](https://img.shields.io/github/stars/nicktill/YTRecap?style=social)](https://github.com/nicktill/YTRecap/stargazers) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
YTRecap (https://ytrecap.org) is a web application that fetches a YouTube video's closed captions and passes them to an AI model to generate a summary of the video content. The application is built using Python Flask.

> **Note:** YouTube blocks caption requests from cloud providers (AWS, Google Cloud, Azure), which includes Vercel. On the hosted site the summary is therefore usually written from the video's title and description only. Captions work when you run the app locally.



### light mode
<img width="1145" alt="Screen Shot 2023-04-08 at 2 24 41 AM" src="https://user-images.githubusercontent.com/57879193/230706884-900acd32-9570-4b83-b614-04886a51f3fc.png">

### dark mode
<img width="1105" alt="Screen Shot 2023-04-08 at 2 24 32 AM" src="https://user-images.githubusercontent.com/57879193/230706886-4e05cdfb-53f1-4fa9-85a4-bde11e8b1e1a.png">

### demo
https://user-images.githubusercontent.com/57879193/230707034-093e8767-b339-495c-b039-1bf87d34e784.mov

### Getting Started

```bash
git clone https://github.com/nicktill/YTRecap.git
cd YTRecap/src
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add a free GEMINI_API_KEY (or an OPENAI_KEY)
python3 app.py         # http://localhost:5050
```

Without an AI key, the app runs in **demo mode** and streams a sample summary, so you can
work on the UI without any API keys. Set `YTRECAP_DEMO=1` to force demo mode.

Share links work by swapping the domain: `ytrecap.org/watch?v=VIDEO_ID`.

See [DEPLOY.md](DEPLOY.md) for hosting and cost notes.
