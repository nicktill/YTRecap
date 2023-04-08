# Import necessary libraries
import os
import openai
from flask import Flask, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi, CouldNotRetrieveTranscript
import re
from googleapiclient.discovery import build
import datetime
import isodate
from dotenv import load_dotenv

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
def generateSummaryWithCaptions(captions, summary_length, yt_url, yt_title, yt_description, yt_tags, yt_duration, yt_likes, yt_dislikes):
    # Set default length to 200 tokens
    # Set summary length to default value if user does not select a summary length
    try:
        if summary_length > 500:
            prompt = f"You are an AI assistant for YTRecap, a webapp that provides very comprehensive and lengthy summaries for any provided youtube video (via url). Please provide a extremely long and comprehensive summary based on the closed captions of this yt video provided here:\n\n {captions}\n\n MAKE SURE IT IS AROUND {summary_length} words long.Here is the video link: {yt_url} along with its title: {yt_title}."
        else:
            prompt = f"You are an AI assistant for YTRecap, a webapp that provides very comprehensive and lengthy summaries for any provided youtube video (via url). Please provide a long and comprehensive summary based on the closed captions of this yt video provided here:\n\n {captions}\n\n MAKE SURE IT IS AROUND {summary_length} words long.Here is the video link: {yt_url} along with its title: {yt_title}."

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens= 1500,
            n=1,
            stop=None,
            temperature=0.5,
        )
        # Remove newlines and extra spaces from summary
        summary = response.choices[0].text.strip()
        return summary

    except openai.error.InvalidRequestError:
        # Return error message if summary cannot be generated
        summaryNoCaptions = generateSummaryNoCaptions(summary_length, yt_url, yt_title, yt_description, yt_tags, yt_duration, yt_likes, yt_dislikes)
        return summaryNoCaptions

#  - This is a fallback function to generate a summary when no captions are provided by YouTube
# - This function is called when the video is too long (causes character limit to openAI API, or there are no captions)
def generateSummaryNoCaptions(summary_length, url, yt_title, yt_description, yt_tags, yt_duration, yt_likes, yt_dislikes):
    if summary_length > 500: 
        prompt = "You are an AI assistant for YTRecap, a webapp that provides very comprehensive and lengthy summaries for any provided youtube video (via inputted url). Please provide a extremely long and comprehensive summary about this video \n\n URL: {url} \n\n Make sure summary length approximately {summary_length} words. Please use the title of the video here {yt_title} \n\n and the descripton here: {yt_description} to provide a summary overview of the video"
    else:
        prompt = f"You are an AI assistant for YTRecap, a webapp that provides video summaries based on any inputted youtube URL. You must provide in depth proffesional written summaries encompassing a summary overview for of any video provided. Can you write a summary about this video {url} in approximately {summary_length} words. Please use the title of the video here {yt_title} \n\n and the descripton here: {yt_description} to provide a summary overview of the video"
    print("Parsing API without captions due to long video OR not captions (or both)...")
    try: 
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens= 1500,
            n=1,
            stop=None,
            temperature=0.5,
        )
    except: 
        # Return error message if summary cannot be generated
        summary = "Uh oh! Sorry, we couldn't generate a summary for this video and this error was not handled. Please visit source-code: https://github.com/nicktill/YTRecap/issues and open a new issue if possibe (it is likely due to the content of the yt video description being too long, exceeding the character limit of the OpenAI API).  "
        return summary
    # Remove newlines and extra spaces from summary
    summary = response.choices[0].text.strip()
    return summary

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
            part='snippet,statistics, contentDetails',
            id=video_id
        ).execute()
        
        # Extract video information
        video_info = {
            'title': video_response['items'][0]['snippet']['title'],
            'author': video_response['items'][0]['snippet']['channelTitle'],
            'date': format_date(video_response['items'][0]['snippet']['publishedAt']),
            'view_count': format_view_count(video_response['items'][0]['statistics']['viewCount']),
            'thumbnail': video_response['items'][0]['snippet']['thumbnails']['medium']['url'],
            'description': video_response['items'][0]['snippet']['description'], # Add description
            'tags': video_response['items'][0]['snippet'].get('tags', []), # Add tags
            'duration': format_duration(video_response['items'][0]['contentDetails']['duration']), # Add duration
            'likes': video_response['items'][0]['statistics'].get('likeCount', 0), # Add like count
            'dislikes': video_response['items'][0]['statistics'].get('dislikeCount', 0), # Add dislike count
        }

    else:
        return render_template('index.html', error="Invalid YouTube URL")
    
    # store video info into vars
    yt_title = video_response['items'][0]['snippet']['title']
    summary_length = int(request.form['summary_length'])
    yt_description = video_response['items'][0]['snippet']['description'].replace("\n", " ").strip()
    yt_tags = video_response['items'][0]['snippet'].get('tags', [])
    yt_duration = format_duration(video_response['items'][0]['contentDetails']['duration'])
    yt_likes = video_response['items'][0]['statistics'].get('likeCount', 0)
    yt_dislikes = video_response['items'][0]['statistics'].get('dislikeCount', 0)

    try: 
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        captions = parse_text_info(transcript)
    except:
        captions = None
        
    if captions:
        summary = generateSummaryWithCaptions(captions, summary_length, url, yt_title, yt_description, yt_tags, yt_duration, yt_likes, yt_dislikes)
    else:
        summary = generateSummaryNoCaptions(summary_length, url, yt_title, yt_description, yt_tags, yt_duration, yt_likes, yt_dislikes)

    # Render the result in the template
    return render_template('index.html', video_info=video_info, summary=summary, video_id=video_id, summary_length=summary_length)

# Run Flask app
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
