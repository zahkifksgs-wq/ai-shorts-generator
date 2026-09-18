import os
import json
import time
import subprocess
import whisper
from google import genai

import streamlit as st

# Streamlit secrets se API Key read karega
API_KEY = st.secrets["GEMINI_API_KEY"]

import os
import yt_dlp

def download_video(url, output_path="input_video.mp4"):
    print("\n[Step 1/6] Downloading YouTube Video...")
    
    if os.path.exists(output_path):
        os.remove(output_path)
        
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # Cloud Datacenter Bypassing Config
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web'],
                'skip': ['hls', 'dash']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Primary engine blocked. Retrying with alternative Android client fallback...")
        ydl_opts['extractor_args']['youtube']['player_client'] = ['android_embedded']
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

def extract_audio(video_path="input_video.mp4", audio_path="audio.mp3"):
    print("\n[Step 2/6] Extracting Audio...")
    command = ['ffmpeg', '-y', '-i', video_path, '-vn', '-acodec', 'libmp3lame', '-q:a', '2', audio_path]
    subprocess.run(command, check=True)

def analyze_and_check_risk(audio_path="audio.mp3"):
    print("\n[Step 3/6] Gemini Analysis...")
    audio_file = client.files.upload(file=audio_path)
    
    prompt = """
    Analyze this audio file and return ONLY a JSON object with:
    1. The best viral segment (15-60s) with start_time and end_time (format HH:MM:SS or MM:SS).
    2. Copyright risk assessment.
    
    Format:
    {
        "start_time": "01:02",
        "end_time": "02:02",
        "risk_level": "Low / Medium / High",
        "action_required": "Modification instructions if any"
    }
    """
    
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[audio_file, prompt]
            )
            cleaned_json = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_json)
            return data
        except Exception as e:
            if attempt < max_retries:
                time.sleep(5)
            else:
                raise Exception("Google Gemini API busy. Please try again.")

def crop_and_modify_video(start_time, end_time, risk_level, input_path="input_video.mp4", output_path="short_output.mp4"):
    print("\n[Step 4/6] Processing Video Format...")
    video_filter = "crop=ih*(9/16):ih,scale=1080:1920"
    audio_filter = "anull"

    if risk_level in ["Medium", "High"]:
        video_filter += ",setpts=PTS/1.03"
        audio_filter = "asetrate=44100*1.02,aresample=44100,atempo=1.01"

    command = [
        'ffmpeg', '-y',
        '-ss', start_time,
        '-to', end_time,
        '-i', input_path,
        '-vf', video_filter,
        '-af', audio_filter,
        output_path
    ]
    subprocess.run(command, check=True)

def generate_subtitles_and_burn(video_path="short_output.mp4", final_output="final_short.mp4", font_size=18, font_color="&H00FFFFFF"):
    print("\n[Step 5/6] Generating Subtitles with Whisper...")
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    
    srt_file = "subtitles.srt"
    with open(srt_file, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result['segments'], start=1):
            start = format_time(segment['start'])
            end = format_time(segment['end'])
            text = segment['text'].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    print("\n[Step 6/6] Burning Subtitles...")
    style_str = f"FontSize={font_size},PrimaryColour={font_color},Alignment=2,Outline=1"
    command = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vf', f"subtitles={srt_file}:force_style='{style_str}'",
        '-c:a', 'copy',
        final_output
    ]
    subprocess.run(command, check=True)

def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"