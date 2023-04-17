# YTRecap 
YTRecap (https://ytrecap.org) is a web application that uses the YouTube Data API to retrieve the closed captions of a YouTube video, and then passes them to an AI model to generate a summary of the video content. The application is built using Python Flask


### light mode
<img width="1145" alt="Screen Shot 2023-04-08 at 2 24 41 AM" src="https://user-images.githubusercontent.com/57879193/230706884-900acd32-9570-4b83-b614-04886a51f3fc.png">

### dark mode
<img width="1105" alt="Screen Shot 2023-04-08 at 2 24 32 AM" src="https://user-images.githubusercontent.com/57879193/230706886-4e05cdfb-53f1-4fa9-85a4-bde11e8b1e1a.png">

### demo
https://user-images.githubusercontent.com/57879193/230707034-093e8767-b339-495c-b039-1bf87d34e784.mov

### Getting Started
To use the YT-Recap application, follow these steps:

1. **Clone the repository:**
    ```
    git clone https://github.com/nicktill/YTRecap.git
    ```

2. **Set up virtual environment:**
    ```
    cd yt-recap
    python3 -m venv venv
    source venv/bin/activate (macOS/Linux)
    venv\Scripts\activate (Windows)
    ```

3. **Install required packages:** 
    ```
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**
    Create a file named `.env` in the `/src` directory of the repo to store your YouTube API key and OpenAI API key. 
    The structure should be as follows:
    ```
    YT_KEY='YOUR_YOUTUBE_API_KEY'
    OPENAI_KEY='YOUR_OPENAI_API_KEY'
    ```

5. **Run the application:**
    ```
    cd src
    python3 app.py
    ```


