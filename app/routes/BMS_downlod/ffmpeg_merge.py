import subprocess

def merge_video_audio(video, audio, output):
    cmd = [
        "ffmpeg", "-y",
        "-i", video,
        "-i", audio,
        "-c:v", "copy",
        "-c:a", "aac",
        output
    ]
    return subprocess.call(cmd)