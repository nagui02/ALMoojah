import os
from dotenv import load_dotenv
 
load_dotenv()
 
# ── API Keys ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY  = os.getenv("YOUTUBE_API_KEY")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")

# ── Groq Model ────────────────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Gemini Model (kept for reference) ────────────────────────────────────────
GEMINI_MODEL = "gemini-2.0-flash"
 
# ── Summary language ──────────────────────────────────────────────────────────
SUMMARY_LANGUAGE = "français"
 
# ── Google Trends ─────────────────────────────────────────────────────────────
GOOGLE_TRENDS_CONFIG = {
    "geo":   "TN",
    "hl":    "fr",
    "top_n": 10,
}
 
# ── YouTube Channels ──────────────────────────────────────────────────────────
YOUTUBE_CHANNELS = [
    {
        "name":       "Al Wataniya 1",
        "channel_id": "UCdvWVsmQBROkgcGzVep73oA",
    },
    {
        "name":       "Al Wataniya 2",
        "channel_id": "UCJW9gatYczI191TunQxMGbA",
    },
    {
        "name":       "Al Wataniya News",
        "channel_id": "UC91i-9lIqoiWfmov8FwjLqA",
    },
]
YOUTUBE_MAX_RESULTS = 2
 
# ── Tunisian RSS Sources ───────────────────────────────────────────────────────
RSS_SOURCES = [
    {
        "name":       "Tunis Afrique Presse (TAP) politique",
        "url":        "http://tap.info.tn/fr/feed",
        "scrape_url": "https://www.tap.info.tn/fr/portail%20-%20politique",
        "lang":       "fr",
        "verify_ssl": False,
    },
    {
        "name":       "Tunis Afrique Presse (TAP) economie",
        "url":        "http://tap.info.tn/fr/feed",
        "scrape_url": "https://www.tap.info.tn/fr/portail%20-%20economie",
        "lang":       "fr",
        "verify_ssl": False,
    },
    {
        "name":       "Tunis Afrique Presse (TAP) société",
        "url":        "http://tap.info.tn/fr/feed",
        "scrape_url": "https://www.tap.info.tn/fr/portail%20-%20société",
        "lang":       "fr",
        "verify_ssl": False,
    },
    {
        "name":       "Tunis Afrique Presse (TAP) régions",
        "url":        "http://tap.info.tn/fr/feed",
        "scrape_url": "https://www.tap.info.tn/fr/portail%20-%20régions",
        "lang":       "fr",
        "verify_ssl": False,
    },
    {
        "name":       "Tunis Afrique Presse (TAP) culture & médias",
        "url":        "http://tap.info.tn/fr/feed",
        "scrape_url": "https://www.tap.info.tn/fr/portail%20-%20culture%20et%20médias",
        "lang":       "fr",
        "verify_ssl": False,
    },
    {
        "name":       "Tunis Afrique Presse (TAP) sport",
        "url":        "http://tap.info.tn/fr/feed",
        "scrape_url": "https://www.tap.info.tn/fr/portail%20-%20sports%20fr",
        "lang":       "fr",
        "verify_ssl": False,
    },
    {
        "name":       "Tunisie Numérique",
        "url":        "https://www.tunisienumerique.com/?feed=rss2",
        "scrape_url": "https://www.tunisienumerique.com/actualite-tunisie/tunisie/",
        "lang":       "fr",
        "verify_ssl": True,
    },
    {
        "name":       "Mosaïque FM",
        "url":        "https://www.mosaiquefm.net/fr/rss",
        "scrape_url": "https://www.mosaiquefm.net/fr/",
        "lang":       "fr",
        "verify_ssl": True,
    },
    {
        "name":       "Jawhara FM",
        "url":        "https://www.jawharafm.net/ar/rss",
        "scrape_url": "https://www.jawharafm.net/fr/articles/actualite/6",
        "lang":       "fr",
        "verify_ssl": True,
    },
    {
        "name":       "Business News TN",
        "url":        "https://www.businessnews.com.tn/rss",
        "scrape_url": "https://www.businessnews.com.tn/",
        "lang":       "fr",
        "verify_ssl": True,
    },
]
RSS_MAX_ARTICLES = 10

# ── Article Categories ────────────────────────────────────────────────────────
CATEGORIES = [
        "Politique",
        "Économie",
        "Société",
        "Sport",
        "Culture & Médias",
        "Technologie",
        "International",
        "Environnement",
        "Santé",
        "Tendance",
    ]

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_HTML = "trends_report.html"

COMPANY_PROFILE = {
    "nom":     "3SG Groupe",
    "description": (
        "Groupe tunisien spécialisé dans les médias, la communication digitale, "
        "la production audiovisuelle et les solutions technologiques pour entreprises."
    ),
    "secteurs": [
        "médias", "presse", "audiovisuel", "communication", "publicité",
        "digital", "technologie", "production", "événementiel",
    ],
    "mots_cles_metier": [
        "télévision", "radio", "journal", "web", "réseaux sociaux", "streaming",
        "agence", "campagne", "contenu", "marque", "audience", "annonceur",
        "droits", "licence", "régulation", "HAICA", "presse écrite",
    ],
    "risques_surveilles": [
        "réglementation médias", "grève", "censure", "loi presse",
        "concurrence étrangère", "baisse publicité", "crise économique",
        "dette", "chômage", "tensions sociales",
    ],
    "opportunites_cibles": [
        "festival", "événement", "lancement produit", "partenariat",
        "appel d'offres", "subvention", "expansion africaine",
        "numérisation", "intelligence artificielle", "startup",
    ],
}
 