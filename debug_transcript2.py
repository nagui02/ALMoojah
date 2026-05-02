# debug_transcript2.py
from youtube_transcript_api import YouTubeTranscriptApi

VIDEO_ID = "mpSwJ8pg4wo"

try:
    transcript_list = YouTubeTranscriptApi.list_transcripts(VIDEO_ID)
    t    = transcript_list.find_transcript(["ar"])
    segs = t.fetch()
    text = " ".join(s["text"] for s in segs)

    print(f"✅ Transcript fetched — {len(text)} chars")
    print(f"\n📝 Preview (first 500 chars):\n{text[:500]}")
    print(f"\n📝 Preview (last 200 chars):\n...{text[-200:]}")

except Exception as e:
    print(f"❌ Error: {e}")