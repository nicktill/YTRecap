import os
import openai
from flask import Flask, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi
import re

app = Flask(__name__)

# Initialize the OpenAI API client
openai.api_key = os.getenv("OPENAI_API_KEY")

def parse_text_info(input_list):
    pattern = re.compile(r"'text':\s+'(?:\[[^\]]*\]\s*)?([^']*)'")
    output = ""
    for item in input_list:
        match = pattern.search(str(item))
        if match:
            text = match.group(1).strip()
            output += " ".join(text.split()) + " "
    return output.strip()

def generate_summary(captions):
    prompt = f"These are captions for a youtube video, can you provide a summary on this youtube video based on the closed captions provided here:\n\n{captions}\n"
    
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.5,
    )

    summary = response.choices[0].text.strip()
    return summary

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
        captions = parse_text_info(transcript)
        summary = generate_summary(captions)        
        return render_template('index.html', summary=summary)
    else:
        error = 'Invalid YouTube URL'
        return render_template('index.html', error=error)
    
if __name__ == '__main__':
    app.run(debug=True)
