# debug_transcript.py
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

VIDEO_ID = "mpSwJ8pg4wo"
LANG_PRIORITY = ["ar", "fr", "en"]

try:
    transcript_list = YouTubeTranscriptApi.list_transcripts(VIDEO_ID)
    for lang in LANG_PRIORITY:
        try:
            t    = transcript_list.find_transcript([lang])
            segs = t.fetch()
            text = " ".join(s["text"] for s in segs)
            print(f"✅ Fetched [{lang}] — {len(text)} chars")
            print(f"📝 Preview:\n{text[:300]}...")
            break
        except Exception:
            continue
except Exception as e:
    print(f"❌ Error: {e}")