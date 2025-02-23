import os
import multiprocessing
from moviepy.editor import ImageClip, AudioFileClip


# Get the number of available CPU cores
threads = multiprocessing.cpu_count()

# Ensure the output folder exists
output_folder = "store"
os.makedirs(output_folder, exist_ok=True)

# Background image and audio file
image_file = os.path.join("contents","background.png")
audio_file = os.path.join("contents", "music.mp3")

# Load audio and get its duration
audio = AudioFileClip(audio_file)
audio_duration = audio.duration  # Match video length to audio length

# Create a video clip from the image
video = ImageClip(image_file, duration=audio_duration)

# Resize and ensure full-screen 1080×1920
video = video.resize(width=1080)  # Resize width first
if video.h < 1920:
    video = video.resize(height=1920)  # Resize height if it's too small

# Crop to exactly 1080×1920
video = video.crop(x1=0, y1=(video.h - 1920) // 2, width=1080, height=1920)

# Reduce brightness (Multiply by a factor < 1 to darken)
video = video.fx(lambda clip: clip.fl_image(lambda frame: (frame * 0.2).astype("uint8")))

# Set audio to the video
video = video.set_audio(audio)

# Define output file path
output_video = os.path.join(output_folder, "video.mp4")

# Export final video using all CPU cores
video.write_videofile(
    output_video,
    fps=30,
    codec="libx264",
    audio_codec="aac",
    threads=threads,
    preset="ultrafast",  # Faster encoding
    ffmpeg_params=["-crf", "23"]  # Balanced quality & compression
)

print(f"✅ Video created successfully using {threads} CPU cores: {output_video}")
