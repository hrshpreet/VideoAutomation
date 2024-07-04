import requests
import os
import json
import random
from dotenv import load_dotenv, dotenv_values
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from moviepy.editor import *

load_dotenv()


def load_json(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

titles_hooks = load_json("titles_hooks.json")["titles_hooks"]
end_slides = load_json("end_slide.json")["end_slides"]
random_title_hook = random.choice(titles_hooks)
random_end_slide = random.choice(end_slides)



def fetch_images(query, api_key, cse_id, num_images=10):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": cse_id,
        "key": api_key,
        "searchType": "image",
        "num": num_images
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        image_urls = [item["link"] for item in data.get("items", [])]
        return image_urls
    else:
        print("Error:", response.status_code, response.text)
        return []

def download_images(image_urls, download_folder="images"):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    
    valid_image_paths = []
    
    for idx, url in enumerate(image_urls):
        response = requests.get(url)
        if response.status_code == 200:
            image_path = os.path.join(download_folder, f"image_{idx + 1}.jpg")
            with open(image_path, "wb") as file:
                file.write(response.content)
            # Verify if the image is valid
            try:
                Image.open(image_path).verify()
                valid_image_paths.append(image_path)
            except UnidentifiedImageError:
                print(f"Skipping invalid image: {image_path}")
                os.remove(image_path)
    
    return valid_image_paths



def resize_and_crop(image, target_width, target_height):
    # Resize the image to fit height
    aspect_ratio = image.width / image.height
    new_height = target_height
    new_width = int(new_height * aspect_ratio)
    image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Crop the image to fit width
    left = (new_width - target_width) / 2
    right = (new_width + target_width) / 2
    image = image.crop((left, 0, right, target_height))
    
    return image



def create_slide(image_path, text, slide_path, target_width, target_height, font_path="arial.ttf", font_size=60):
    try:
        image = Image.open(image_path).convert("RGBA")
    except UnidentifiedImageError:
        print(f"Cannot identify image file {image_path}")
        return
    
    image = resize_and_crop(image, target_width, target_height)
    
    # Create a dark background
    background = Image.new("RGBA", image.size, (0, 0, 0, 200))
    image = Image.alpha_composite(image, background)
    
    txt = Image.new("RGBA", image.size, (255, 255, 255, 0))

    draw = ImageDraw.Draw(txt)
    font = ImageFont.truetype(font_path, font_size)

    # Function to wrap text
    def wrap_text(text, font, max_width):
        lines = []
        words = text.split()
        while words:
            line = ''
            while words and draw.textlength(line + words[0], font=font) <= max_width:
                line = f"{line} {words.pop(0)}".strip()
            lines.append(line)
        return "\n".join(lines)

    wrapped_text = wrap_text(text, font, image.width - 200)
    
    text_bbox = draw.textbbox((0, 0), wrapped_text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

    position = ((image.width - text_width) // 2, (image.height - text_height) // 2)

    draw.multiline_text(position, wrapped_text, fill="white", font=font, align="center")

    combined = Image.alpha_composite(image, txt)
    combined = combined.convert("RGB")
    combined.save(slide_path)



def generate_tts_audio(text, filename):
    voice_api = os.getenv("VOICE_RSS_KEY")
    url = f"http://api.voicerss.org/?key={voice_api}&hl=en-ca&v=Mason&src={text}"
    tts = requests.get(url)

    if tts.status_code == 200:
        with open(filename, "wb") as f:
            f.write(tts.content)
        print("Audio saved successfully.")
    else:
        print(f"Error occurred: {tts.status_code}")


def create_video(slide_paths, audio_paths, audio_durations, output_path="output_video.mp4", music_path='./music/emotional-music2.mp3', padding=1):
    video_clips = []
    
    for slide_path, audio_path, audio_duration in zip(slide_paths, audio_paths, audio_durations):
        try:
            slide_duration = audio_duration
            clip = VideoFileClip(slide_path).set_duration(slide_duration)
            audio = AudioFileClip(audio_path).subclip(0, min(slide_duration, audio_duration))
            clip = clip.set_audio(audio)
            video_clips.append(clip)
        except OSError as e:
            print(f"Error processing {slide_path} or {audio_path}: {e}")
            continue

    if not video_clips:
        print("No valid clips to create the video.")
        return

    # cross-fade-in
    video_fx_list = [video_clips[0]]
    idx = video_clips[0].duration - padding
    
    for video in video_clips[1:]:
        video_fx_list.append(video.set_start(idx).crossfadein(padding))
        idx += video.duration - padding

    final_video = CompositeVideoClip(video_fx_list)

    # Add background music
    try:
        bg_audio = AudioFileClip(music_path).subclip(0, final_video.duration).fx(afx.volumex, 0.5)
        new_audio = CompositeAudioClip([final_video.audio, bg_audio])
        final_video = final_video.set_audio(new_audio)
    except OSError as e:
        print(f"Error processing background music: {e}")

    try:
        final_video.write_videofile(output_path, fps=24)
    except Exception as e:
        print(f"Error writing video file: {e}")



def delete_slides(slide_paths):
    for slide_path in slide_paths:
        if os.path.exists(slide_path):
            os.remove(slide_path)
            print(f"Deleted {slide_path}")
        else:
            print(f"File {slide_path} not found.")



def load_progress(progress_file="progress.json"):
    if os.path.exists(progress_file):
        with open(progress_file, "r") as file:
            data = json.load(file)
            return data.get("last_index", -1)
    else:
        return -1



def save_progress(last_index, progress_file="progress.json"):
    with open(progress_file, "w") as file:
        json.dump({"last_index": last_index}, file)



def create_video_from_script(text, video_title, output_path="output_video.mp4", target_width=1080, target_height=1920):
    API_KEY = os.getenv("IMAGES_API_KEY")
    CSE_ID = os.getenv("IMAGES_CSE_ID")
    
    # Break input text :)
    lines = []
    current_line = ""
    for char in text:
        current_line += char
        if char in ['.', '?', '!', ':']:
            lines.append(current_line.strip())
            current_line = ""
            
    if current_line:
        lines.append(current_line.strip())
        
    
    # Get images
    image_urls = fetch_images(video_title, API_KEY, CSE_ID)
    valid_image_paths = download_images(image_urls)
    random.shuffle(valid_image_paths)

    if len(valid_image_paths) < min(len(lines), 5):
        print("Not enough valid images to create slides.")
        return "Not enough valid images to create slides."
    
    
    # Create Slides
    slides_info = []
    for idx, line in enumerate(lines):
        slide_info = {
            "text": line,
            "image": valid_image_paths[idx % len(valid_image_paths)],
            "slide": f"slide_{idx + 1}.jpg"
        }
        slides_info.append(slide_info)
        create_slide(slide_info["image"], slide_info["text"], slide_info["slide"], target_width, target_height)
    
    
    # audio
    audio_files = []
    audio_durations = []
    
    for idx, slide_info in enumerate(slides_info):
        audio_path = f"slide_{idx + 1}.mp3"
        generate_tts_audio(slide_info["text"], audio_path)
        audio_files.append(audio_path)

        audio_clip = AudioFileClip(audio_path)
        audio_durations.append(audio_clip.duration)
        audio_clip.close()

    # final video
    slide_paths = [slide_info["slide"] for slide_info in slides_info]
    create_video(slide_paths, audio_files, audio_durations, output_path)

    delete_slides(slide_paths)
    delete_slides(audio_files)

    return output_path


if __name__ == "__main__":
    text = "Your input text goes here. This can be a longer paragraph or multiple sentences."
    video_title = "Jesus"
    output_video_path = create_video_from_script(text, video_title, target_width=1920, target_height=1080)
    print(f"Video created: {output_video_path}")