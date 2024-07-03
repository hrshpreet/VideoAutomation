# VideoAutomation

Hey there! Welcome to **VideoAutomation**! 🎉 This project is all about making **Short video creation** super easy by automatically combining images, text, and audio into awesome videos. 

## Features

- 🌐 **Image Fetching:** Grabs images from the web based on chosen topic.
- 🎤 **Text-to-Speech (TTS):** Creates audio clips using TTS.
- ✏️ **Text Overlay:** Adds captions to the video.
- 🎬 **Video Creation:** Brings together images, text, and audio into a polished video.

## Setup

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/hrshpreet/VideoAutomation.git
    cd VideoAutomation
    ```

2. **Install Required Packages:**

    ```bash
    pip install requests gtts Pillow moviepy python-dotenv
    ```

3. **Create a `.env` File:**

    Create a `.env` file in the project root directory and add your API keys:

    ```plaintext
    IMAGES_API_KEY=google_custom_search_api_key
    IMAGES_CSE_ID=google_custom_search_engine_id
    VOICE_RSS_KEY=voice_rss_api_key
    ```

4. **JSON Files:**

    Following JSON files are in the project directory:
    - `titles_hooks.json` - For intro
    - `end_slide.json` - For outro
    - `quotes.json` - Main Content

## Future Plans:

- 🌍 Enhance TTS Voices: Adding more depth to TTS using Bark.
- 📺 Platform Integration: Direct uploads to platforms like YouTube.
- Maybe a UI
