# YT-Recap


<img width="501" alt="Screen Shot 2023-03-01 at 7 50 34 PM" src="https://user-images.githubusercontent.com/57879193/222302371-0f88a1b1-c13f-4937-beeb-c535fa1b84f7.png">

YTRecap is an application that uses the YouTube Data API to retrieve the closed captions of a YouTube video, and then passes them to an AI model to generate a summary of the video content. The application is built using Python Flask

# Getting Started
To use the YT-Recap application, follow these steps:

# Clone this repository to your local machine.

Install the dependencies by running npm install in the root directory of the project.

Create a virtual environment and install the required Python packages by running pip install -r requirements.txt in the python directory of the project.

Set up a Google Cloud project and enable the YouTube Data API. Follow the instructions provided by Google to obtain a YouTube Data API key.

Create a new file called .env.local in the root directory of the project, and add the following lines to the file:

```
NEXT_PUBLIC_YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY
```
Replace YOUR_YOUTUBE_API_KEY with your own YouTube Data API key.

Start the development server by running npm run dev in the root directory of the project. The application should now be running at http://localhost:3000.
