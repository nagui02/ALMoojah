# debug_whisper.py
import os
import subprocess
import tempfile
import yt_dlp
import whisper

FFMPEG = r"C:\Users\nejiy\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
os.environ["PATH"] += f";{os.path.dirname(FFMPEG)}"

VIDEO_URL   = "https://www.youtube.com/watch?v=mpSwJ8pg4wo"
CLIP_SECS   = 180  # only transcribe first 3 minutes

print("⬇️  Downloading audio...")
with tempfile.TemporaryDirectory() as tmp:
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(tmp, "audio.%(ext)s"),
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(VIDEO_URL, download=True)
        print(f"✅ Title : {info['title']}")
        print(f"✅ Views : {info.get('view_count', 0):,}")

    # Find downloaded audio file
    audio_file = next(
        os.path.join(tmp, f) for f in os.listdir(tmp) if f.startswith("audio")
    )
    print(f"✅ Audio : {audio_file}")

    # Cut to first 3 minutes
    short_audio = os.path.join(tmp, "audio_short.wav")
    print(f"\n✂️  Cutting to first {CLIP_SECS//60} minutes...")
    subprocess.run([
        FFMPEG,
        "-i", audio_file,
        "-t", str(CLIP_SECS),
        "-ar", "16000",   # 16kHz mono — optimal for Whisper
        "-ac", "1",
        short_audio,
        "-y", "-loglevel", "quiet"
    ], check=True)
    print(f"✅ Short audio ready")

    # Transcribe
    print(f"\n🎙️  Transcribing with Whisper (base model)...")
    model  = whisper.load_model("base")
    result = model.transcribe(short_audio, fp16=False)

    print(f"✅ Language : {result['language']}")
    print(f"✅ Length   : {len(result['text'])} chars")
    print(f"\n📝 Preview:\n{result['text'][:500]}...")