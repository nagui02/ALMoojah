"""
main.py — Point d'entrée principal
Pipeline :
  1. Fetch         → collecte depuis toutes les sources
  2. Pre-classify  → catégorise par mots-clés (sans API)
  3. Cap           → garde TOP_PER_CATEGORY articles par catégorie
  4. Summarize     → résumé + catégorie finale + score via Groq (1 appel batch)
  5. Report        → génère le dashboard HTML
"""

import sys
import re
import time
from collections import defaultdict
from fetcher    import fetch_all
from summarizer import summarize_all
from reporter   import build_report, open_report
from config     import CATEGORIES

TOP_PER_CATEGORY = 2

# ── Keyword map ───────────────────────────────────────────────────────────────
KEYWORD_MAP = {
    "Politique": [
        "gouvernement", "ministre", "parlement", "président", "saied", "politique",
        "election", "parti", "sénat", "assemblée", "diplomatie", "ambassadeur",
        "décret", "loi", "constitution", "coopération", "sommet", "hafedh",
        "conseil", "présidence", "réforme", "décision", "autorité",
    ],
    "Économie": [
        "économie", "économique", "bourse", "dinar", "inflation", "budget",
        "investissement", "entreprise", "banque", "finances", "export", "import",
        "pib", "croissance", "dette", "chômage", "emploi", "salaire", "augmentation",
        "business", "commerce", "marché", "douane", "fiscalité", "startup",
        "chèque", "financement", "privatisation", "production", "industrie",
    ],
    "Sport": [
        "foot", "football", "ligue", "match", "arbitre", "club africain", "espérance",
        "sfaxien", "olympique", "sport", "basket", "volley", "handball", "natation",
        "athlétisme", "coupe", "championnat", "bal", "fifa", "caf", "can",
        "stade", "joueur", "entraîneur", "classement", "score", "victoire",
        "défaite", "tournoi", "équipe", "sélection", "nul", "but", "penalty",
        # Arabic sport keywords (for YouTube)
        "كرة", "دوري", "بطولة", "رياضة", "نتيجة", "هدف", "مباراة",
    ],
    "Société": [
        "société", "social", "grève", "syndicat", "ugtt", "travailleur", "éducation",
        "école", "université", "étudiant", "famille", "femme", "jeunesse", "justice",
        "tribunal", "avocat", "crime", "accident", "sécurité", "police", "prison",
        "migration", "logement", "transport", "route", "manifestation", "protestation",
        "retraite", "pension", "aide", "allocation", "formation",
    ],
    "Culture & Médias": [
        "culture", "festival", "musique", "film", "cinéma", "théâtre", "art",
        "concert", "livre", "littérature", "patrimoine", "dougga", "carthage",
        "média", "radio", "télévision", "journaliste", "presse", "exposition",
        "prix", "récompense", "spectacle", "artiste", "chanteur", "acteur",
    ],
    "Technologie": [
        "technologie", "numérique", "digital", "intelligence artificielle", "ia",
        "application", "internet", "cybersécurité", "data", "innovation",
        "tech", "informatique", "telecom", "4g", "5g", "réseau", "logiciel",
        "plateforme", "algorithme", "cloud", "blockchain", "robot", "drone",
        "startup", "incubateur", "hackathon", "développeur", "programmation",
    ],
    "International": [
        "international", "monde", "europe", "france", "usa", "états-unis", "trump",
        "israel", "palestine", "liban", "algérie", "maroc", "libye", "afrique",
        "onu", "union européenne", "otan", "guerre", "conflit", "sanctions",
        "iran", "russie", "ukraine", "chine", "arabie", "qatar", "turquie",
        "diplomatie", "accord", "traité", "mondial", "global",
    ],
    "Environnement": [
        "environnement", "climatique", "climat", "sécheresse", "eau", "forêt",
        "incendie", "pollution", "énergie", "solaire", "renouvelable", "température",
        "météo", "agriculture", "récolte", "irrigation", "biodiversité",
        "déchets", "recyclage", "oasis", "barrage", "ressources naturelles",
    ],
    "Santé": [
        "santé", "médecin", "hôpital", "maladie", "vaccin", "covid", "médical",
        "pharmacie", "cancer", "diabète", "épidémie", "traitement", "chirurgie",
        "clinique", "patient", "infirmier", "urgence", "médicament", "dépistage",
        "généraliste", "spécialiste", "soins", "bien-être",
    ],
    "Tendance": [],
}


# ── Pre-classifier ────────────────────────────────────────────────────────────

def _quick_classify(article: dict) -> str:
    text = (article.get("title", "") + " " + article.get("snippet", "")).lower()
    text = re.sub(r"[^\w\s]", " ", text)

    scores = defaultdict(int)
    for category, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text:
                # Multi-word keywords count more
                scores[category] += len(kw.split())

    if scores:
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
    return "Tendance"


# ── Cap per category ──────────────────────────────────────────────────────────

def _cap_per_category(articles: list, top_n: int = TOP_PER_CATEGORY) -> list:
    youtube = [a for a in articles if "YouTube" in a.get("source", "")]
    trends  = [a for a in articles if "Google Trends" in a.get("source", "")]
    rest    = [a for a in articles if
               "YouTube" not in a.get("source", "") and
               "Google Trends" not in a.get("source", "")]

    buckets = defaultdict(list)
    for a in rest:
        cat = _quick_classify(a)
        a["pre_category"] = cat
        buckets[cat].append(a)

    selected = []
    print("  📂  Pré-classification par catégorie :")
    for cat in CATEGORIES:
        if cat == "Tendance":
            continue
        items   = buckets.get(cat, [])
        kept    = items[:top_n]
        dropped = len(items) - len(kept)
        selected.extend(kept)
        if items:
            drop_str = f", ignoré {dropped}" if dropped else ""
            print(f"     {cat:<22} → {len(kept)} gardé{drop_str} (sur {len(items)})")
        else:
            print(f"     {cat:<22} → 0 (aucun article trouvé)")

    tendance = buckets.get("Tendance", [])
    kept     = tendance[:top_n]
    selected.extend(kept)
    print(f"     {'Tendance':<22} → {len(kept)} gardé (sur {len(tendance)})")

    for a in youtube:
        a["pre_category"] = _quick_classify(a)
    selected.extend(youtube)
    print(f"     {'YouTube':<22} → {len(youtube)} (toujours inclus)")

    for a in trends:
        a["pre_category"] = "Tendance"
    selected.extend(trends)
    print(f"     {'Google Trends':<22} → {len(trends)} (toujours inclus)")

    return selected


# ── Helpers ───────────────────────────────────────────────────────────────────

def _banner():
    print("""
╔══════════════════════════════════════════════════════╗
║        🇹🇳  Veille Médiatique Tunisie  🇹🇳            ║
║       Agent d'actualités — déclenchement manuel      ║
╚══════════════════════════════════════════════════════╝
""")

def _separator(label: str = ""):
    width = 54
    if label:
        pad = (width - len(label) - 2) // 2
        print(f"\n{'─' * pad} {label} {'─' * pad}\n")
    else:
        print(f"\n{'─' * width}\n")

def _elapsed(start: float) -> str:
    secs = int(time.time() - start)
    m, s = divmod(secs, 60)
    return f"{m}m {s:02d}s" if m else f"{s}s"


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run(top_per_category: int = TOP_PER_CATEGORY, skip_summarize: bool = False):
    total_start = time.time()
    _banner()

    _separator("ÉTAPE 1 — COLLECTE")
    fetch_start = time.time()
    articles    = fetch_all()
    if not articles:
        print("❌ Aucun article collecté.")
        sys.exit(1)
    print(f"⏱  Collecte terminée en {_elapsed(fetch_start)}.")
    print(f"📰  {len(articles)} articles bruts récupérés.\n")

    _separator("ÉTAPE 2 — SÉLECTION PAR CATÉGORIE")
    articles = _cap_per_category(articles, top_n=top_per_category)
    print(f"\n📌  {len(articles)} articles sélectionnés.\n")

    _separator("ÉTAPE 3 — RÉSUMÉ IA (Groq)")
    if skip_summarize:
        print("⚠️  Mode rapide — résumé IA désactivé.")
        for a in articles:
            a.setdefault("summary",  a.get("snippet", "")[:200] or a.get("title", ""))
            a.setdefault("category", a.get("pre_category", "Tendance"))
            a.setdefault("score",    2)
        enriched = articles
    else:
        summarize_start = time.time()
        enriched        = summarize_all(articles)
        print(f"⏱  Résumé terminé en {_elapsed(summarize_start)}.")

    _separator("ÉTAPE 4 — RAPPORT HTML")
    path = build_report(enriched)
    open_report(path)

    _separator("TERMINÉ")
    print(f"✅  Pipeline complet en {_elapsed(total_start)}.")
    print(f"📄  Rapport : {path}")
    print(f"📊  Articles traités : {len(enriched)}")

    from collections import Counter
    cats = Counter(a.get("category", "?") for a in enriched)
    print("\n📂  Répartition finale par catégorie :")
    for cat, count in cats.most_common():
        bar = "█" * count
        print(f"    {cat:<22} {bar} ({count})")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="🇹🇳 Veille Médiatique Tunisie — Agent d'actualités IA"
    )
    parser.add_argument("--top", type=int, default=TOP_PER_CATEGORY,
                        help=f"Articles par catégorie (défaut: {TOP_PER_CATEGORY})")
    parser.add_argument("--fast", action="store_true",
                        help="Mode rapide sans résumé IA")
    args = parser.parse_args()
    run(top_per_category=args.top, skip_summarize=args.fast)