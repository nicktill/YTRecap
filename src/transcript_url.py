import os
import openai
from flask import Flask, render_template, request
from googleapiclient.discovery import build
import datetime
import isodate
from dotenv import load_dotenv
import re

# Initialize Flask app and load environment variables
app = Flask(__name__)
load_dotenv()

# Set OpenAI API key
openai.api_key = os.environ.get('OPENAI_KEY')

# Function to format duration string into a human-readable format
def format_duration(duration_string):
    duration = isodate.parse_duration(duration_string)
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# Function to format view count into a human-readable format
def format_view_count(view_count):
    view_count = int(view_count)
    if view_count >= 1000000:
        return f"{view_count // 1000000}M"
    elif view_count >= 10000:
        return f"{view_count // 1000}K"
    else:
        return str(view_count)

# Function to format date string into a human-readable format
def format_date(date_string):
    date = datetime.datetime.fromisoformat(date_string[:-1])
    return date.strftime("%B %d, %Y")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def get_summary():
    url = request.form['url']
    match = re.search(r"(?<=v=)[\w-]+|[\w-]+(?<=/v/)|(?<=youtu.be/)[\w-]+", url)
    if match:
        video_id = match.group(0)
        # must use YT KEY for the information in video_info below
        youtube = build('youtube', 'v3', developerKey=os.environ.get('YT_KEY'))
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        ).execute()

        # Extract video informtion
        video_info = {
            'title': video_response['items'][0]['snippet']['title'],
            'author': video_response['items'][0]['snippet']['channelTitle'],
            'date': format_date(video_response['items'][0]['snippet']['publishedAt']),
            'view_count': format_view_count(video_response['items'][0]['statistics']['viewCount']),
            'thumbnail': video_response['items'][0]['snippet']['thumbnails']['medium']['url'],
        }
        video_title = video_response['items'][0]['snippet']['title']

    summary_length = request.form.get('summary_length')
    print("summary length here <=====================", summary_length)
    summary = generate_summary(url, summary_length, video_title)
    return render_template('index.html', video_info=video_info, summary=summary)

# Function to generate summary using OpenAI API
def generate_summary(youtube_url, summary_length, video_title):
    prompt = f"Can you summarize this video {youtube_url} in around {summary_length} words, the title of the video is {video_title}?"
    print("prompt here <=====================", prompt)
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000,
        n=1,
        stop=None,
        temperature=0.5,
    )
    summary = response.choices[0].text.strip()
    return summary

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
