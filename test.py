import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx, AudioFileClip
import multiprocessing

os.environ["OMP_NUM_THREADS"] = str(multiprocessing.cpu_count())  # Adjust based on your CPU

# Load video and remove audio
video = VideoFileClip("video.mp4").without_audio()

# Load background music, trim to 11 sec & reduce volume by 50%
audio = AudioFileClip("music_0.wav").subclip(0, 11)

# Attach modified music to video
final_video = video.set_audio(audio)

# Save final video
final_video.write_videofile(
    "video1.mp4",
    fps=30,
    codec="libx264",
    audio_codec="aac",
    threads=multiprocessing.cpu_count(),
    preset="ultrafast",
    ffmpeg_params=["-crf", "23"]
)

