from flask import Flask, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi
import re

app = Flask(__name__)

def parse_text_info(input_list):
    pattern = re.compile(r"'text':\s+'(?:\[[^\]]*\]\s*)?([^']*)'")
    output = ""
    for item in input_list:
        match = pattern.search(str(item))
        if match:
            text = match.group(1).strip()
            output += " ".join(text.split()) + " "
    return output.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def get_transcript():
    url = request.form['url']
    match = re.search(r"(?<=v=)[\w-]+|[\w-]+(?<=/v/)|(?<=youtu.be/)[\w-]+", url)
    if match:
        video_id = match.group(0)
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        summary = parse_text_info(transcript)
        return render_template('index.html', summary=summary)
    else:
        error = 'Invalid YouTube URL'
        return render_template('index.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
