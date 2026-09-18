import streamlit as st
import os
from main import download_video, extract_audio, analyze_and_check_risk, crop_and_modify_video, generate_subtitles_and_burn

st.set_page_config(page_title="AI Shorts Generator Pro", page_icon="🎬", layout="wide")

st.title("🎬 AI Shorts Generator Pro")
st.markdown("Automated YouTube Shorts Clipper with Custom Subtitles & Batch Processing")

# Sidebar for Custom Subtitle Options
st.sidebar.header("🎨 Subtitle Styling Settings")
font_size = st.sidebar.slider("Font Size", min_value=12, max_value=28, value=18)
color_choice = st.sidebar.selectbox("Subtitle Color", ["White", "Yellow", "Cyan", "Green"])

color_map = {
    "White": "&H00FFFFFF",
    "Yellow": "&H0000FFFF",
    "Cyan": "&H00FFFF00",
    "Green": "&H0000FF00"
}
selected_color = color_map[color_choice]

# Main Interface Tabs
tab1, tab2 = st.tabs(["⚡ Single Video Processing", "📦 Batch / Playlist Processing"])

with tab1:
    uploaded_file = st.file_uploader("Upload MP4 Video directly (Recommended Fallback):", type=["mp4"])
    url = st.text_input("OR Enter Single YouTube Video Link:")
    
    if st.button("Generate Short", type="primary"):
        if uploaded_file is not None or url:
            with st.status("Processing Video...", expanded=True) as status:
                if uploaded_file is not None:
                    st.write("📥 Saving uploaded file...")
                    with open("input_video.mp4", "wb") as f:
                        f.write(uploaded_file.read())
                else:
                    st.write("📥 Downloading video from YouTube...")
                    download_video(url)
                
                st.write("🎵 Extracting audio...")
                extract_audio()
                
                st.write("🤖 Gemini analyzing viral clip & copyright risk...")
                ai_data = analyze_and_check_risk()
                
                st.write("✂️ Cropping video & applying copyright safety filters...")
                crop_and_modify_video(ai_data['start_time'], ai_data['end_time'], ai_data['risk_level'])
                
                st.write("📝 Auto-transcribing and burning custom subtitles...")
                generate_subtitles_and_burn(font_size=font_size, font_color=selected_color)
                
                status.update(label="Short Ready!", state="complete", expanded=False)
                
            st.success("Short processing completed!")
            if os.path.exists("final_short.mp4"):
                st.video("final_short.mp4")
                with open("final_short.mp4", "rb") as file:
                    st.download_button("Download Short", data=file, file_name="AI_Short.mp4", mime="video/mp4")

with tab2:
    urls_input = st.text_area("Enter Multiple YouTube Links (One per line):", height=150)
    if st.button("Process Batch Queue"):
        urls = [u.strip() for u in urls_input.split('\n') if u.strip()]
        if urls:
            st.info(f"Total Videos in Queue: {len(urls)}")
            for idx, item_url in enumerate(urls, start=1):
                st.write(f"--- Processing Video {idx}/{len(urls)} ---")
                try:
                    video_out = f"input_{idx}.mp4"
                    audio_out = f"audio_{idx}.mp3"
                    short_out = f"short_{idx}.mp4"
                    final_out = f"final_short_{idx}.mp4"
                    
                    download_video(item_url, output_path=video_out)
                    extract_audio(video_path=video_out, audio_path=audio_out)
                    ai_data = analyze_and_check_risk(audio_path=audio_out)
                    crop_and_modify_video(ai_data['start_time'], ai_data['end_time'], ai_data['risk_level'], input_path=video_out, output_path=short_out)
                    generate_subtitles_and_burn(video_path=short_out, final_output=final_out, font_size=font_size, font_color=selected_color)
                    
                    st.success(f"Video {idx} Completed: {final_out}")
                    if os.path.exists(final_out):
                        st.video(final_out)
                except Exception as e:
                    st.error(f"Error processing video {idx}: {e}")