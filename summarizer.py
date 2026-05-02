"""
summarizer.py — v7 (Groq batch mode)
Sends ALL articles in a single Groq API call instead of one per article.
Benefits:
  - Uses only 1 API request → no per-minute rate limit issues
  - Extremely fast (Groq runs on custom LPU hardware)
  - Completely free, no credit card needed
  - Falls back gracefully per-article if response is missing or malformed
"""

import json
import re
import time
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL, CATEGORIES, COMPANY_PROFILE

client = Groq(api_key=GROQ_API_KEY)

MAX_RETRIES = 3


# ── Batch prompt ──────────────────────────────────────────────────────────────

def _build_batch_prompt(articles: list) -> str:
    categories_str = ", ".join(CATEGORIES)
    cp = COMPANY_PROFILE

    articles_block = ""
    for i, a in enumerate(articles):
        hint = a.get("pre_category", "")
        hint_line = f"\n  INDICE CATÉGORIE: {hint}" if hint else ""
        articles_block += f"""
ARTICLE {i}:
  TITRE   : {a['title']}
  SOURCE  : {a['source']}
  CONTENU : {(a.get('snippet') or '')[:300] or 'Aucun contenu — base-toi sur le titre.'}{hint_line}
"""

    return f"""Tu es un analyste stratégique senior travaillant pour {cp['nom']}.
{cp['nom']} est un {cp['description']}

Ses secteurs d'activité : {', '.join(cp['secteurs'])}.
Ses risques surveillés : {', '.join(cp['risques_surveilles'])}.
Ses opportunités cibles : {', '.join(cp['opportunites_cibles'])}.

On te donne une liste d'articles d'actualité tunisienne ou internationale.

Pour CHAQUE article, tu dois produire :
1. Un résumé de 2 à 3 phrases claires en FRANÇAIS.
2. La catégorie parmi : {categories_str}
3. Un score de pertinence générale pour la Tunisie (1 à 5).
4. Un score d'impact spécifique pour {cp['nom']} (1 à 5) :
   - 5 = impact direct et immédiat sur l'activité de {cp['nom']}
   - 4 = opportunité ou risque significatif à surveiller de près
   - 3 = information utile pour la veille sectorielle
   - 2 = pertinence indirecte ou faible
   - 1 = aucun impact prévisible
5. Une phrase d'analyse d'impact (max 25 mots) expliquant POURQUOI cet article
   est ou n'est pas important pour {cp['nom']}. Commence par "Pour {cp['nom']} :"

{articles_block}

Réponds UNIQUEMENT avec un tableau JSON valide, sans texte autour, sans balises markdown.
Exactement {len(articles)} objets :
[
  {{
    "index": 0,
    "summary": "...",
    "category": "...",
    "score": 3,
    "impact_score": 4,
    "impact_label": "Pour {cp['nom']} : ..."
  }},
  ...
]"""


# ── Fallback for all articles ─────────────────────────────────────────────────

def _apply_fallbacks(articles: list) -> list:
    enriched = []
    for a in articles:
        e = a.copy()
        e["summary"]       = a.get("snippet", "")[:300] or a.get("title", "")
        e["category"]      = a.get("pre_category", "Tendance")
        e["score"]         = 2
        e["impact_score"]  = 1
        e["impact_label"]  = ""
        enriched.append(e)
    return enriched


# ── Batch summarize ───────────────────────────────────────────────────────────

def summarize_all(articles: list) -> list:
    if not GROQ_API_KEY:
        print("  [Summarizer] ✗ GROQ_API_KEY manquant — ajoutez-le dans .env")
        return _apply_fallbacks(articles)

    total = len(articles)
    print(f"\n🤖 Envoi de {total} articles à Groq en un seul appel...\n")

    prompt = _build_batch_prompt(articles)

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000,
            )

            raw_text = response.choices[0].message.content.strip()
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            parsed = json.loads(raw_text)

            if not isinstance(parsed, list):
                raise ValueError("Response is not a JSON array")

            lookup = {item["index"]: item for item in parsed if "index" in item}

            enriched = []
            success  = 0
            fallback = 0

            for i, article in enumerate(articles):
                e = article.copy()
                if i in lookup:
                    item = lookup[i]
                    e["summary"]       = item.get("summary", "").strip() or article.get("snippet", "")[:300]
                    e["category"]      = item.get("category", article.get("pre_category", "Tendance")).strip()
                    e["score"]         = int(item.get("score", 3))
                    e["impact_score"]  = int(item.get("impact_score", 1))
                    e["impact_label"]  = item.get("impact_label", "").strip()
                    success += 1
                    impact_star = "🔴" if e["impact_score"] >= 4 else "🟡" if e["impact_score"] == 3 else "⚪"
                    print(f"  [{i+1:02}/{total}] ✓ [{e['category']}] ⭐{e['score']} {impact_star}Impact:{e['impact_score']} — {article['title'][:50]}...")
                    print(f"          💬 {e['summary'][:90]}...")
                    if e["impact_label"]:
                        print(f"          🏢 {e['impact_label'][:90]}")
                else:
                    e["summary"]  = article.get("snippet", "")[:300] or article.get("title", "")
                    e["category"] = article.get("pre_category", "Tendance")
                    e["score"]    = 2
                    fallback += 1
                    print(f"  [{i+1:02}/{total}] ↩ Fallback — {article['title'][:55]}...")

                enriched.append(e)

            enriched.sort(key=lambda x: x.get("score", 0), reverse=True)
            print(f"\n✅ Terminé — {success} résumés Groq, {fallback} fallbacks.\n")
            return enriched

        except json.JSONDecodeError as e:
            print(f"  ✗ JSON invalide (tentative {attempt+1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(3)
            continue

        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < MAX_RETRIES - 1:
                print(f"  ⏳ Rate limit Groq — attente 30s...")
                time.sleep(30)
                continue
            print(f"  ✗ Erreur Groq : {error_str[:120]}")
            if attempt == MAX_RETRIES - 1:
                return _apply_fallbacks(articles)

    return _apply_fallbacks(articles)


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_articles = [
        {
            "title":        "Les avocats décrètent la grève générale",
            "source":       "Business News TN",
            "link":         "https://businessnews.com.tn/test",
            "snippet":      "Les avocats tunisiens ont voté une grève générale, dénonçant la crise du système judiciaire.",
            "pre_category": "Société",
        },
        {
            "title":        "Ligue 1 : désignation des arbitres pour la 28e journée",
            "source":       "Mosaïque FM",
            "link":         "https://mosaiquefm.net/test",
            "snippet":      "La LFP a désigné les arbitres pour la 28e journée du championnat tunisien.",
            "pre_category": "Sport",
        },
        {
            "title":        "Bryan Adams arrive à Tunis pour ses concerts à Dougga",
            "source":       "TAP",
            "link":         "https://tap.info.tn/test",
            "snippet":      "La star internationale Bryan Adams est arrivée à Tunis pour deux concerts au théâtre antique de Dougga.",
            "pre_category": "Culture & Médias",
        },
    ]

    results = summarize_all(test_articles)
    print("\n─── RÉSULTATS ───")
    for a in results:
        print(f"\n[{a['category']}] ⭐{a['score']} — {a['title']}")
        print(f"  {a['summary']}")