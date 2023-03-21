# Import required libraries
import os
import openai
from flask import Flask, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi
import re
from googleapiclient.discovery import build
import datetime
import isodate

# Initialize the Flask app
app = Flask(__name__)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
print("API KEY HERE" , openai.api_key)

# Define a function to format video duration
def format_duration(duration_string):
    # Parse the duration string
    duration = isodate.parse_duration(duration_string)
    # Convert the duration to total seconds
    total_seconds = int(duration.total_seconds())
    # Extract hours, minutes, and seconds
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    # Format the duration based on the number of hours, minutes, and seconds
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# Define a function to format video view count
def format_view_count(view_count):
    # Convert the view count to an integer
    view_count = int(view_count)
    # Format the view count based on its value
    if view_count >= 1000000:
        return f"{view_count // 1000000}M"
    elif view_count >= 10000:
        return f"{view_count // 1000}K"
    else:
        return str(view_count)

# Define a function to format video publish date
def format_date(date_string):
    # Convert the date string to a datetime object
    date = datetime.datetime.fromisoformat(date_string[:-1])
    # Format the date string
    return date.strftime("%B %d, %Y")

def parse_text_info(input_list):
    # Define a regular expression pattern to match the text information
    pattern = re.compile(r"'text':\s+'(?:\[[^\]]*\]\s*)?([^']*)'")
    # Initialize the output variable
    output = ""
    # Loop through the input list and match the text information
    for item in input_list:
        match = pattern.search(str(item))
        if match:
            text = match.group(1).strip()
            text = text.replace('\n', ' ')
            text = re.sub(' +', ' ', text)
            output += text + " "
    # Return the parsed text information
    return output.strip()

# Define a function to generate a summary of the video based on its closed captions
def generate_summary(captions):
    # Define the prompt for the OpenAI API
    prompt = f"These are captions for a youtube video, can you provide a summary on this youtube video based on the closed captions provided here:\n\n{captions}\n"
    print(prompt)
    # Generate a summary using the OpenAI API
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.5,
    )
    # Extract the summary text from the API response
    summary = response.choices[0].text.strip()
    # Return the summary text
    return summary

# Define the index route for the Flask app
@app.route('/')
def index():
    # Render the index.html template
    return render_template('index.html')

# Define the route for the form submission
@app.route('/', methods=['POST'])
def get_transcript():
    url = request.form['url']
    # Use regular expressions to extract the video ID from the URL
    match = re.search(r"(?<=v=)[\w-]+|[\w-]+(?<=/v/)|(?<=youtu.be/)[\w-]+", url)
    if match:
        # Extract the video ID from the regular expression match
        video_id = match.group(0)
        # Retrieve video information from YouTube Data API
        youtube = build('youtube', 'v3', developerKey=os.getenv("YOUTUBE_API_KEY"))
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        print("YOUTUBE KEY HERE", youtube_api_key)
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        ).execute()
        
        # Extract relevant information from video response
        video_info = {
            'title': video_response['items'][0]['snippet']['title'],
            'author': video_response['items'][0]['snippet']['channelTitle'],
            'date': format_date(video_response['items'][0]['snippet']['publishedAt']),
            'view_count': format_view_count(video_response['items'][0]['statistics']['viewCount']),
            'thumbnail': video_response['items'][0]['snippet']['thumbnails']['medium']['url'],
        }
        # Retrieve the video transcript from YouTube
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # Parse the text information from the transcript
        captions = parse_text_info(transcript)
        print(captions)
        # Generate a summary based on the closed captions
        summary = generate_summary(captions)
        
        # Render the index.html template with the video information and summary
        return render_template('index.html', video_info=video_info, summary=summary)
    else:
        # Render the index.html template with an error message
        error = 'Invalid YouTube URL'
        return render_template('index.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
