import os
import multiprocessing
import pandas as pd
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, vfx

# Input & output folders
output_folder = "upload_videos"
excel_file = "combined.xlsx"  # Excel file with Titles & Quotes
os.makedirs(output_folder, exist_ok=True)  # Ensure output folder exists

videos_dic = {}

# Load Excel file
df = pd.read_excel(excel_file)

df = df.iloc[56:]

# Loop through each row in the Excel file
for index, row in df.iterrows():
    try:
        title = row["Title"]
        arjunas = row["Arjuna's Question"]
        krishnas = row["Krishna's Answer"]
        output_video = os.path.join(output_folder, f"{index + 1}.mp4")  # Use index as filename

        videos_dic[index + 1] = title

        # Load video
        final_video = VideoFileClip("video.mp4" if index%2==0 else "video1.mp4")

        # Define colors
        arjuna_color = "yellow"
        krishna_color = "cyan"
        text_color = "white"

        # Create text clips
        arjuna_text_clip = TextClip(f'<span foreground="yellow"><b>Arjuna:</b></span> {arjunas}', color=text_color, font="Arial", fontsize=30, method="Pango", size=(1000, 1920))
        krishna_text_clip = TextClip(f'<span foreground="cyan"><b>Krishna:</b></span> {krishnas}', color=text_color, font="Arial", fontsize=30, method="Pango", size=(1000, 1920))

        print(arjuna_text_clip.h)
        

        arjuna_text_clip = arjuna_text_clip.set_position(("center",550)).set_duration(final_video.duration)
        krishna_text_clip = krishna_text_clip.set_position(("center",700)).set_duration(final_video.duration)

        # Apply 3-second fade-in effect to Krishna text clip
        krishna_text_clip = krishna_text_clip.fx(vfx.fadein, duration=4)

        # Overlay text clips onto the video
        final_video = CompositeVideoClip([final_video, arjuna_text_clip, krishna_text_clip])

        # Save final video
        final_video.write_videofile(
            output_video,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            threads=multiprocessing.cpu_count(),
            preset="ultrafast",
            ffmpeg_params=["-crf", "23"]
        )

        print(f"✅ Processed: video saved as {output_video}")

        # Cleanup
        final_video.close()

        print(videos_dic)

        if index == 60:
            break

    except Exception as e:
        print(f"❌ Error processing row {index + 1}: {e}")

print("🎥 All videos processed successfully!")