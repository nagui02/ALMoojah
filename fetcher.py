"""
fetcher.py — v7
Changes in this version:
  #1 → YouTube fetching via yt-dlp (no API key, no quota)
  #2 → Whisper fallback when youtube-transcript-api fails
  #3 → Audio clipped to first 3 min before Whisper
  #4 → Skip videos longer than 30 minutes
"""

import re
import os
import subprocess
import tempfile
import feedparser
import requests
import hashlib
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import (
    GOOGLE_TRENDS_CONFIG,
    YOUTUBE_CHANNELS,
    YOUTUBE_MAX_RESULTS,
    RSS_SOURCES,
    RSS_MAX_ARTICLES,
)

REQUEST_TIMEOUT          = 20
MAX_WORKERS              = 5
RETRIES                  = 2
TRANSCRIPT_MAX_CHARS     = 1500
TRANSCRIPT_LANG_PRIORITY = ["ar", "fr", "en"]
MAX_VIDEO_DURATION       = 1800   # 30 minutes in seconds

# ── ffmpeg path ───────────────────────────────────────────────────────────────
FFMPEG_PATH = r"C:\Users\nejiy\Downloads\ffmpeg-master-latest-win64-gpl\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
os.environ["PATH"] += f";{os.path.dirname(FFMPEG_PATH)}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,ar;q=0.7",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_html(raw: str) -> str:
    if not raw:
        return ""
    text = BeautifulSoup(raw, "html.parser").get_text(separator=" ")
    return " ".join(text.split())[:1000]


def _clean_title(title: str) -> str:
    return re.sub(r'^\d+', '', title).strip()


def _make_article(title: str, source: str, link: str, snippet: str = "", has_transcript: bool = False) -> dict:
    return {
        "title":          _clean_title(title),
        "source":         source,
        "link":           link.strip(),
        "snippet":        snippet.strip(),
        "has_transcript": has_transcript,
    }


def _get(url: str, verify: bool = True):
    for attempt in range(RETRIES):
        try:
            return requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=verify)
        except requests.RequestException:
            if attempt < RETRIES - 1:
                time.sleep(1)
    return None


def _hash(article: dict) -> str:
    key = (article["title"] + article["link"]).lower().strip()
    return hashlib.md5(key.encode()).hexdigest()


# ── Whisper transcript ────────────────────────────────────────────────────────

def _get_transcript_whisper(video_id: str) -> tuple[str, str]:
    """Downloads audio and transcribes with Whisper (first 3 min only)."""
    try:
        import yt_dlp
        import whisper

        url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"    🎙 Whisper fallback — downloading audio...")

        with tempfile.TemporaryDirectory() as tmp:
            ydl_opts = {
                "format":      "bestaudio/best",
                "outtmpl":     os.path.join(tmp, "audio.%(ext)s"),
                "quiet":       True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info     = ydl.extract_info(url, download=False)
                duration = info.get("duration", 0) or 0
                if duration > MAX_VIDEO_DURATION:
                    print(f"    ⏭ Skipping — too long ({duration//60} min > 30 min)")
                    return "", ""
                ydl.extract_info(url, download=True)

            audio_file = next(
                (os.path.join(tmp, f) for f in os.listdir(tmp) if f.startswith("audio")),
                None
            )
            if not audio_file:
                return "", ""

            short_audio = os.path.join(tmp, "audio_short.wav")
            subprocess.run([
                FFMPEG_PATH,
                "-i", audio_file,
                "-t", "180",
                "-ar", "16000",
                "-ac", "1",
                short_audio,
                "-y", "-loglevel", "quiet"
            ], check=True)

            print(f"    🎙 Transcribing with Whisper...")
            model  = whisper.load_model("base")
            result = model.transcribe(short_audio, fp16=False)
            text   = result["text"].strip()
            lang   = result.get("language", "ar")

            return " ".join(text.split())[:TRANSCRIPT_MAX_CHARS], lang

    except Exception as e:
        print(f"    ⚠ Whisper failed — {str(e)[:80]}")
        return "", ""


# ── YouTube transcript (API first, Whisper fallback) ─────────────────────────

def _get_transcript(video_id: str) -> tuple[str, str]:
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for lang in TRANSCRIPT_LANG_PRIORITY:
            try:
                t    = transcript_list.find_transcript([lang])
                segs = t.fetch()
                text = " ".join(s["text"] for s in segs)
                return " ".join(text.split())[:TRANSCRIPT_MAX_CHARS], lang
            except Exception:
                continue
        for t in transcript_list:
            try:
                segs = t.fetch()
                text = " ".join(s["text"] for s in segs)
                return " ".join(text.split())[:TRANSCRIPT_MAX_CHARS], t.language_code
            except Exception:
                continue
    except (TranscriptsDisabled, NoTranscriptFound):
        pass
    except Exception:
        pass

    return _get_transcript_whisper(video_id)


# ── YouTube via yt-dlp (no API key needed) ────────────────────────────────────

def _fetch_channel_videos_ytdlp(channel: dict) -> list[dict]:
    """Fetches latest videos from a channel using yt-dlp — no API key needed."""
    import yt_dlp

    articles   = []
    name       = channel["name"]
    channel_id = channel["channel_id"]
    url        = f"https://www.youtube.com/channel/{channel_id}/videos"

    print(f"  [YouTube/yt-dlp] Fetching {name}...")

    ydl_opts = {
        "quiet":          True,
        "no_warnings":    True,
        "extract_flat":   True,           # don't download, just get metadata
        "playlistend":    YOUTUBE_MAX_RESULTS,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info  = ydl.extract_info(url, download=False)
            items = info.get("entries", []) or []
            print(f"  [YouTube/yt-dlp] {len(items)} videos found — {name}")

            for item in items:
                if not item:
                    continue
                video_id = item.get("id", "")
                title    = item.get("title", "Sans titre")
                link     = f"https://www.youtube.com/watch?v={video_id}"
                duration = item.get("duration") or 0

                # Skip videos > 30 min
                if duration > MAX_VIDEO_DURATION:
                    print(f"    ⏭ Skipping — too long ({duration//60} min) — {title[:40]}...")
                    continue

                transcript_text, lang_code = _get_transcript(video_id)
                if transcript_text:
                    snippet        = transcript_text
                    has_transcript = True
                    print(f"    ✓ Transcript [{lang_code}] — {title[:50]}...")
                else:
                    snippet        = item.get("description", "")[:400] if item.get("description") else ""
                    has_transcript = False
                    print(f"    ⚠ No transcript — {title[:50]}...")

                articles.append(_make_article(
                    title=title, source=f"YouTube – {name}",
                    link=link, snippet=snippet, has_transcript=has_transcript,
                ))

    except Exception as e:
        print(f"  [YouTube/yt-dlp] ✗ {name} — {str(e)[:100]}")

    return articles


def fetch_youtube() -> list[dict]:
    articles = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(_fetch_channel_videos_ytdlp, ch) for ch in YOUTUBE_CHANNELS]
        for f in as_completed(futures):
            articles.extend(f.result())

    transcribed = sum(1 for a in articles if a["has_transcript"])
    print(f"  [YouTube] ✅ {len(articles)} videos | {transcribed} with transcripts.\n")
    return articles


# ── RSS parser ────────────────────────────────────────────────────────────────

def _parse_rss(response, source_name: str) -> list[dict]:
    feed    = feedparser.parse(response.content)
    entries = feed.entries[:RSS_MAX_ARTICLES]
    results = []
    for entry in entries:
        raw = (
            entry.get("summary", "")
            or entry.get("description", "")
            or (entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "")
        )
        results.append(_make_article(
            title=entry.get("title", "Sans titre"),
            source=source_name,
            link=entry.get("link", ""),
            snippet=_clean_html(raw),
        ))
    return results


# ── Web scraping fallback ─────────────────────────────────────────────────────

def _scrape_homepage(url: str, source_name: str, verify: bool = True) -> list[dict]:
    articles = []
    resp = _get(url, verify=verify)
    if not resp or resp.status_code != 200:
        code = resp.status_code if resp else "no response"
        print(f"  [Scrape] ✗ {source_name} — HTTP {code}")
        return []

    soup       = BeautifulSoup(resp.text, "html.parser")
    base       = url.rstrip("/")
    candidates = []

    for article in soup.find_all("article", limit=20):
        a       = article.find("a", href=True)
        heading = article.find(["h1", "h2", "h3", "h4"])
        if a and heading:
            candidates.append((heading.get_text(strip=True), a["href"]))

    if len(candidates) < 3:
        for tag in soup.find_all(["h2", "h3", "h4"], limit=40):
            a = tag.find("a", href=True)
            if a:
                candidates.append((tag.get_text(strip=True), a["href"]))

    if len(candidates) < 3:
        for a in soup.find_all("a", href=True, limit=80):
            text = a.get_text(strip=True)
            if len(text) > 40:
                candidates.append((text, a["href"]))

    seen_links  = set()
    seen_titles = set()

    for title, href in candidates:
        title = _clean_title(title)
        if len(title) < 20:
            continue

        if href.startswith("http"):
            link = href
        elif href.startswith("/"):
            parsed = urlparse(url)
            link   = f"{parsed.scheme}://{parsed.netloc}{href}"
        else:
            link = f"{base}/{href}"

        if link in seen_links or title in seen_titles:
            continue

        seen_links.add(link)
        seen_titles.add(title)
        articles.append(_make_article(title=title, source=source_name, link=link))

        if len(articles) >= RSS_MAX_ARTICLES:
            break

    print(f"  [Scrape] {'✓' if articles else '⚠'} {len(articles)} articles — {source_name}")
    return articles


# ── Single source (RSS → scrape fallback) ────────────────────────────────────

def _fetch_single_source(source: dict) -> list[dict]:
    name   = source["name"]
    verify = source.get("verify_ssl", True)

    print(f"  [RSS] Trying {name}...")
    resp = _get(source["url"], verify=verify)

    if resp and resp.status_code == 200:
        articles = _parse_rss(resp, name)
        if articles:
            print(f"  [RSS] ✓ {len(articles)} articles — {name}")
            return articles
        print(f"  [RSS] ⚠ Feed empty — scraping fallback for {name}")
    else:
        code = resp.status_code if resp else "no response"
        print(f"  [RSS] ✗ HTTP {code} — scraping fallback for {name}")

    if scrape_url := source.get("scrape_url"):
        return _scrape_homepage(scrape_url, name, verify=verify)
    return []


def fetch_rss() -> list[dict]:
    articles = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(_fetch_single_source, src) for src in RSS_SOURCES]
        for f in as_completed(futures):
            articles.extend(f.result())
    return articles


# ── Google Trends ─────────────────────────────────────────────────────────────

def fetch_google_trends() -> list[dict]:
    articles = []
    try:
        from pytrends.request import TrendReq
        print("  [Google Trends] Fetching...")
        pytrends = TrendReq(hl="fr-FR", tz=60, timeout=(10, 25))

        try:
            df       = pytrends.trending_searches(pn="tunisie")
            keywords = df[0].head(GOOGLE_TRENDS_CONFIG["top_n"]).tolist()
            if not keywords:
                raise ValueError("empty")
        except Exception:
            print("  [Google Trends] Fallback: related queries...")
            pytrends.build_payload(["Tunisie", "Tunisia news"], geo="TN", timeframe="now 1-d")
            related  = pytrends.related_queries()
            keywords = []
            for v in related.values():
                top = v.get("top")
                if top is not None and not top.empty:
                    keywords += top["query"].head(5).tolist()
            keywords = list(dict.fromkeys(keywords))[:GOOGLE_TRENDS_CONFIG["top_n"]]

        for kw in keywords:
            articles.append(_make_article(
                title=kw,
                source="Google Trends TN",
                link=f"https://trends.google.com/trends/explore?q={kw.replace(' ', '+')}&geo=TN",
                snippet=f"Tendance de recherche en Tunisie : {kw}",
            ))
        print(f"  [Google Trends] ✓ {len(articles)} trends.")
    except Exception as e:
        print(f"  [Google Trends] ✗ Skipped — {e}")
    return articles


# ── Main entry point ──────────────────────────────────────────────────────────

def fetch_all() -> list[dict]:
    print("\n📡 Fetching from all sources...\n")

    raw = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fetch_google_trends): "Trends",
            executor.submit(fetch_youtube):       "YouTube",
            executor.submit(fetch_rss):           "RSS",
        }
        for f in as_completed(futures):
            raw.extend(f.result())

    seen, unique = set(), []
    for a in raw:
        h = _hash(a)
        if h not in seen:
            seen.add(h)
            unique.append(a)

    transcribed = sum(1 for a in unique if a.get("has_transcript"))
    print(f"✅ Done — {len(unique)} articles total | {transcribed} YouTube transcripts.\n")
    return unique


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = fetch_all()
    for i, a in enumerate(results, 1):
        tag = "📝" if a.get("has_transcript") else "🔗"
        print(f"{i:02}. {tag} [{a['source']}] {a['title']}")
        print(f"     🔗 {a['link']}")
        if a["snippet"]:
            print(f"     💬 {a['snippet'][:120]}...")
        print()