import re
from youtube_transcript_api import YouTubeTranscriptApi

def parse_text_info(input_list):
    pattern = re.compile(r"'text':\s+'(?:\[[^\]]*\]\s*)?([^']*)'")
    output = ""
    for item in input_list:
        match = pattern.search(str(item))
        if match:
            text = match.group(1).strip()
            output += " ".join(text.split()) + " "
    return output.strip()

# Ask user for YouTube URL
url = input("Enter a YouTube URL: ")

# Extract video ID from URL using regex
match = re.search(r"(?<=v=)[\w-]+|[\w-]+(?<=/v/)|(?<=youtu.be/)[\w-]+", url)
if match:
    video_id = match.group(0)
else:
    print("Invalid YouTube URL")
    exit()

# Get transcript for video and summarize it
transcript = YouTubeTranscriptApi.get_transcript(video_id)
summary = parse_text_info(transcript)
print(summary)
