# Import necessary libraries
import os
import openai
from flask import Flask, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi
import re
from googleapiclient.discovery import build
import datetime
import isodate
from dotenv import load_dotenv
import boto3
import json

# Initialize Flask app and load environment variables
app = Flask(__name__)
load_dotenv()


ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY_ID') # Get the access key from the environment variables
SECRET_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY') # Get the secret key from the environment variables

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

# Function to parse transcript and extract text information
def parse_text_info(input_list):
    #regex to remove timestamps and speaker names
    pattern = re.compile(r"'text':\s+'(?:\[[^\]]*\]\s*)?([^']*)'")
    output = ""
    for item in input_list:
        match = pattern.search(str(item))
        if match:
            text = match.group(1).strip()
            text = text.replace('\n', ' ')
            text = re.sub(' +', ' ', text)
            output += text + " "
    return output.strip()

# Function to generate summary using OpenAI API
def generate_summary(captions):
    # Create boto3 Session with AWS credentials
    session = boto3.Session(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='us-east-2'
    )

    runtime = session.client("sagemaker-runtime") # Create a SageMaker runtime client
    endpoint_name = "huggingface-pytorch-inference-2023-03-29-21-31-55-850" # The name of the endpoint that you created
    content_type = "application/json" # The MIME type of the input data in the request body
    payload = json.dumps({"inputs": captions}) # Create the payload that you will send to the endpoint

    response = runtime.invoke_endpoint( # Invoke the endpoint
        EndpointName=endpoint_name, 
        ContentType=content_type, 
        Body=payload
    )

    #parse the response
    result = json.loads(response["Body"].read().decode()) # Get the result from the response
    return result

# Render index page
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    return render_template('index.html')

# Get transcript and generate summary
@app.route('/', methods=['POST'], defaults={'path': ''})
@app.route('/<path:path>', methods=['POST'])
def get_transcript(path):
    # Get video URL from user input
    url = request.form['url']
    # Extract video ID from URL using regex
    match = re.search(r"(?<=v=)[\w-]+|[\w-]+(?<=/v/)|(?<=youtu.be/)[\w-]+", url)
    # If match is found, get video information from YouTube API
    if match:
        video_id = match.group(0)
        youtube = build('youtube', 'v3', developerKey=os.environ.get('YT_KEY'))
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        ).execute()
        # Extract video information
        video_info = {
            'title': video_response['items'][0]['snippet']['title'],
            'author': video_response['items'][0]['snippet']['channelTitle'],
            'date': format_date(video_response['items'][0]['snippet']['publishedAt']),
            'view_count': format_view_count(video_response['items'][0]['statistics']['viewCount']),
            'thumbnail': video_response['items'][0]['snippet']['thumbnails']['medium']['url'],
        }

    # Get transcript and parse text
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    captions = parse_text_info(transcript)
# Generate summary based on user-selected summary length
    summary_length = request.form['summary_length']
    if summary_length:
        summary_length = int(summary_length)
    else:
        summary_length = int(200)
    summary = generate_summary(captions)
    # Render the result in the template
    return render_template('index.html', video_info=video_info, summary=summary, video_id=video_id)

# Run Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
