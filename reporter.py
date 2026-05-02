"""
reporter.py — Moojah Dashboard Generator
Generates the full Moojah HTML dashboard with real pipeline articles injected.
Score 5 → Viral | 4 → À la une | 3 → Important | 2 → Modéré | 1 → Minime
"""

import json
import os
import base64
import webbrowser
from datetime import datetime
from pathlib import Path
from config import OUTPUT_HTML, COMPANY_PROFILE

# ── Logo embed (base64 so HTML is fully standalone) ───────────────────────────
def _logo_b64() -> str:
    """Returns base64 data URI for the Moojah logo."""
    candidates = [
        Path(__file__).parent / "logo_final2.png",
        Path(__file__).parent / "logo final2.png",
        Path("logo_final2.png"),
        Path("logo final2.png"),
        Path(__file__).parent / "tn.png",
        Path(__file__).parent / "tn.png",
        Path("tn.png"),
        Path("tn.png"),
        Path(__file__).parent / "fr.png",
        Path(__file__).parent / "fr.png",
        Path("fr.png"),
        Path("fr.png"),
        Path(__file__).parent / "us.png",
        Path(__file__).parent / "us.png",
        Path("us.png"),
        Path("us.png"),
    ]
    for p in candidates:
        if p.exists():
            data = base64.b64encode(p.read_bytes()).decode()
            return f"data:image/png;base64,{data}"
    return ""   # fallback: no logo if file not found

# ── Score → frequency badge mapping ──────────────────────────────────────────
def _freq(score: int) -> dict:
    mapping = {
        5: {"key": "viral",     "label": "Viral",      "cls": "freq-viral"},
        4: {"key": "une",       "label": "À la une",   "cls": "freq-une"},
        3: {"key": "important", "label": "Important",  "cls": "freq-important"},
        2: {"key": "modere",    "label": "Modéré",     "cls": "freq-modere"},
        1: {"key": "minime",    "label": "Minime",     "cls": "freq-minime"},
    }
    return mapping.get(score, mapping[2])

# ── Category → emoji tag ──────────────────────────────────────────────────────
CATEGORY_EMOJI = {
    "Politique":        "🏛️",
    "Économie":         "💰",
    "Société":          "🏡",
    "Sport":            "⚽",
    "Culture & Médias": "🎬",
    "Technologie":      "💻",
    "International":    "🌍",
    "Environnement":    "🌱",
    "Santé":            "💊",
    "Tendance":         "📈",
    "Justice":          "⚖️",
    "Défense":          "🪖",
    "Business":         "🏢",
    "Science":          "🔬",
    "Énergie":          "⚡",
    "Transport":        "🚗",
    "Agriculture":      "🚜",
    "Gastronomie":      "🍽️",
    "Culture":          "🎬",
    "Musique":          "🎵",
    "Célébrités":       "🌟",
    "Divers":           "🗞️",
    "Événements":       "🎉",
    "Tendances":        "📈"
}

def _cat_emoji(cat: str) -> str:
    return CATEGORY_EMOJI.get(cat, "🗞️")

# ── Build JS articles array from pipeline output ──────────────────────────────
def _build_js_articles(articles: list) -> str:
    now = datetime.now()
    js_items = []
    for a in articles:
        cat      = a.get("category", a.get("pre_category", "Tendance"))
        score    = int(a.get("score", 2))
        freq     = _freq(score)
        summary  = a.get("summary", a.get("snippet", ""))[:500]
        title    = a.get("title", "").replace('"', '\\"').replace('\n', ' ')
        summary  = summary.replace('"', '\\"').replace('\n', ' ')
        source   = a.get("source", "").replace('"', '\\"')
        link     = a.get("link", "#")
        emoji    = _cat_emoji(cat)
        has_tr   = a.get("has_transcript", False)

        impact_score = int(a.get("impact_score", 1))
        impact_label = (a.get("impact_label", "") or "").replace('"', '\\\"').replace("\n", " ")
        impact_icons = {5: "🔴 Critique", 4: "🟠 Important", 3: "🟡 À surveiller", 2: "🔵 Faible", 1: "⚪ Neutre"}
        impact_txt   = impact_icons.get(impact_score, "⚪ Neutre")

        js_items.append(f"""{{
      title:       "{title}",
      summary:     "{summary}",
      category:    "{cat}",
      catEmoji:    "{emoji}",
      source:      "{source}",
      link:        "{link}",
      freqKey:     "{freq['key']}",
      freqLbl:     "{freq['label']}",
      freqCls:     "{freq['cls']}",
      score:        {score},
      date:        "{now.strftime('%d/%m/%Y')}",
      transcript:  {"true" if has_tr else "false"},
      impactScore:  {impact_score},
      impactCls:   "impact-{impact_score}",
      impactTxt:   "{impact_txt}",
      impactLabel: "{impact_label}"
    }}""")

    return "const ARTICLES = [\n  " + ",\n  ".join(js_items) + "\n];"


# ── HTML generator ────────────────────────────────────────────────────────────
def _build_html(articles: list) -> str:
    logo_uri   = _logo_b64()
    js_data    = _build_js_articles(articles)
    generated  = datetime.now().strftime("%d/%m/%Y à %H:%M")
    count      = len(articles)

    logo_tag = (
        f'<img src="{logo_uri}" alt="Moojah" class="logo-image">'
        if logo_uri else
        '<span class="logo-text-fallback">🌊 Moojah</span>'
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Moojah Actualités</title>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Noto+Sans+Arabic:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --navy: #2d4a8a;
    --navy-dark: #1e3470;
    --beige: #f5efe0;
    --beige-dark: #ede3cc;
    --sidebar-border: #e0d5b8;
    --card-bg: #fdf3c8;
    --card-border: #f0e08a;
    --white: #ffffff;
    --text: #1a1a2e;
    --text-light: #5a5a7a;
    --rubrique-bg: #ffffff;
    --rubrique-hover: #f0f4ff;
    --rubrique-text: #1a1a2e;
    --tag-bg: #ffffff;
    --tag-border: #e8e0c8;
    --section-title: #1e3470;
    --slider-track: #d4c9a8;
    --slider-val-color: #2d4a8a;
    --viral: #e74c3c;
    --une: #f39c12;
    --important: #f1c40f;
    --modere: #27ae60;
    --minime: #3498db;
    --shadow: 0 4px 20px rgba(45,74,138,0.10);
    --shadow-hover: 0 8px 32px rgba(45,74,138,0.18);
    --radius: 18px;
    --radius-sm: 10px;
    --card-body-color: #3a3a5a;
    --card-date-color: #1e3470;
    --no-results-color: #5a5a7a;
  }}

  body.dark {{
    --beige: #12131a;
    --beige-dark: #1a1c28;
    --sidebar-border: #2a2d42;
    --card-bg: #1e2236;
    --card-border: #2e3454;
    --white: #252840;
    --text: #e8eaf6;
    --text-light: #8890b8;
    --rubrique-bg: #252840;
    --rubrique-hover: #2e3460;
    --rubrique-text: #c8ccee;
    --tag-bg: #454a6e;
    --tag-border: #6c77c8;
    --section-title: #8aabff;
    --slider-track: #2e3454;
    --slider-val-color: #8aabff;
    --shadow: 0 4px 20px rgba(0,0,0,0.35);
    --shadow-hover: 0 8px 32px rgba(0,0,0,0.5);
    --card-body-color: #a8aed0;
    --card-date-color: #8aabff;
    --no-results-color: #8890b8;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Sora', sans-serif;
    background: var(--beige);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    transition: background 0.35s, color 0.35s;
  }}

  /* ── HEADER ── */
  header {{
    background: linear-gradient(135deg, var(--navy-dark) 0%, var(--navy) 100%);
    padding: 0 32px;
    height: 72px;
    display: flex;
    align-items: center;
    gap: 24px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 4px 24px rgba(30,52,112,0.28);
  }}

  .logo-area {{ display: flex; align-items: center; gap: 10px; text-decoration: none; flex-shrink: 0; }}
  .logo-image {{ height: 54px; width: auto; display: block; }}
  .logo-text-fallback {{ font-size: 1.7rem; font-weight: 800; color: #fff; }}

  .header-meta {{
    font-size: 0.75rem;
    color: rgba(255,255,255,0.55);
    white-space: nowrap;
    flex-shrink: 0;
  }}

  .search-wrap {{
    flex: 1;
    max-width: 520px;
    position: relative;
    margin: 0 auto;
  }}

  .search-wrap input {{
    width: 100%;
    padding: 10px 44px 10px 18px;
    border-radius: 50px;
    border: none;
    background: rgba(255,255,255,0.15);
    color: #fff;
    font-family: 'Sora', sans-serif;
    font-size: 0.95rem;
    outline: none;
    transition: background 0.2s;
    backdrop-filter: blur(8px);
  }}

  .search-wrap input::placeholder {{ color: rgba(255,255,255,0.65); }}
  .search-wrap input:focus {{ background: rgba(255,255,255,0.25); }}
  .search-icon {{ position: absolute; right: 14px; top: 50%; transform: translateY(-50%); font-size: 1.1rem; color: rgba(255,255,255,0.7); pointer-events: none; }}

  .theme-toggle {{ display: flex; align-items: center; gap: 8px; margin-left: auto; flex-shrink: 0; }}
  .theme-icon {{ font-size: 1.2rem; }}
  .toggle-track {{ width: 44px; height: 24px; background: rgba(255,255,255,0.25); border-radius: 50px; position: relative; cursor: pointer; transition: background 0.2s; }}
  .toggle-knob {{ width: 18px; height: 18px; background: #fff; border-radius: 50%; position: absolute; top: 3px; left: 3px; transition: left 0.2s; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }}

  /* ── LAYOUT ── */
  .layout {{ display: flex; flex: 1; min-height: 0; }}

  /* ── SIDEBAR ── */
  aside {{
    width: 268px;
    flex-shrink: 0;
    background: var(--beige-dark);
    padding: 28px 18px 28px 22px;
    display: flex;
    flex-direction: column;
    gap: 28px;
    border-right: 1.5px solid var(--sidebar-border);
    min-height: calc(100vh - 72px);
    position: sticky;
    top: 72px;
    height: calc(100vh - 72px);
    overflow-y: auto;
    transition: background 0.35s, border-color 0.35s;
  }}

  .sidebar-section h3 {{
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--section-title);
    margin-bottom: 14px;
    letter-spacing: -0.2px;
    transition: color 0.35s;
  }}

  /* Période Slider */
  .period-slider-wrap {{ padding: 4px 0; }}
  .slider-labels {{ display: flex; justify-content: space-between; font-size: 0.78rem; color: var(--text-light); margin-bottom: 6px; }}
  input[type=range] {{
    -webkit-appearance: none;
    width: 100%;
    height: 5px;
    border-radius: 10px;
    background: var(--slider-track);
    outline: none;
    cursor: pointer;
  }}
  .slider-value {{ text-align: center; font-size: 0.82rem; font-weight: 700; color: var(--slider-val-color); margin-top: 6px; }}

  .stats-row {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }}

  .stat-chip {{
    background: var(--rubrique-bg);
    border: 1.5px solid var(--tag-border);
    border-radius: 50px;
    padding: 4px 12px;
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--navy);
    white-space: nowrap;
  }}

  .rubrique-grid {{ display: flex; flex-wrap: wrap; gap: 7px; }}

  .rubrique-btn {{
    background: var(--rubrique-bg);
    border: 2px solid transparent;
    border-radius: 50px;
    padding: 5px 11px;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--rubrique-text);
    cursor: pointer;
    transition: border-color 0.15s, box-shadow 0.15s, background 0.15s, color 0.35s;
    white-space: nowrap;
  }}

  .rubrique-btn:hover {{ box-shadow: 0 2px 10px rgba(45,74,138,0.15); background: var(--rubrique-hover); }}
  .rubrique-btn.active {{ border-color: var(--navy); background: var(--rubrique-hover); color: var(--navy); }}

  /* Score filter (Stars) */
  .score-row {{ display: flex; flex-wrap: wrap; gap: 6px; }}

  .score-btn {{
    border: 2px solid transparent;
    border-radius: 50px;
    padding: 4px 12px;
    font-size: 0.76rem;
    font-weight: 700;
    color: #fff;
    cursor: pointer;
    opacity: 0.6;
    transition: opacity 0.15s, border-color 0.15s;
    white-space: nowrap;
  }}

  .score-btn.active {{ opacity: 1; border-color: #fff; }}
  .score-btn.freq-viral     {{ background: var(--viral); }}
  .score-btn.freq-une       {{ background: var(--une); color: #333; }}
  .score-btn.freq-important {{ background: var(--important); color: #333; }}
  .score-btn.freq-modere    {{ background: var(--modere); }}
  .score-btn.freq-minime    {{ background: var(--minime); }}

  /* Langues */
  .langue-row {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .flag-btn {{
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 7px 14px;
    border-radius: 10px;
    background: var(--rubrique-bg);
    border: 2px solid transparent;
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--rubrique-text);
    cursor: pointer;
    transition: all 0.15s;
  }}
  .flag-btn.active {{ border-color: var(--navy); background: var(--rubrique-hover); color: var(--navy); }}

  /* ── MAIN FEED ── */
  main {{
    flex: 1;
    padding: 28px 28px 40px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 18px;
    max-height: calc(100vh - 72px);
  }}

  .card {{
    background: var(--card-bg);
    border: 1.5px solid var(--card-border);
    border-radius: var(--radius);
    padding: 20px 22px 18px;
    box-shadow: var(--shadow);
    transition: box-shadow 0.2s, transform 0.2s, background 0.35s, border-color 0.35s;
    animation: fadeIn 0.35s ease both;
  }}

  .card:hover {{ box-shadow: var(--shadow-hover); transform: translateY(-2px); }}

  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}

  .card-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 12px;
  }}

  .card-title {{ font-size: 1.05rem; font-weight: 700; color: var(--text); margin-right: 4px; flex: 1; min-width: 0; }}

  .card-tags {{ display: flex; flex-wrap: wrap; gap: 6px; flex-shrink: 0; }}

  .tag {{
    background: var(--tag-bg);
    border-radius: 50px;
    padding: 3px 11px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text);
    border: 1.5px solid var(--tag-border);
    transition: background 0.35s, border-color 0.35s, color 0.35s;
  }}

  .card-meta {{ display: flex; align-items: center; gap: 10px; flex-shrink: 0; }}

  .freq-badge {{
    border-radius: 8px;
    padding: 4px 14px;
    font-size: 0.8rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 0.2px;
    white-space: nowrap;
  }}

  .freq-viral     {{ background: var(--viral); }}
  .freq-une       {{ background: var(--une); color: #333 !important; }}
  .freq-important {{ background: var(--important); color: #333 !important; }}
  .freq-modere    {{ background: var(--modere); }}
  .freq-minime    {{ background: var(--minime); }}

  .card-date {{ font-size: 0.9rem; font-weight: 700; color: var(--card-date-color); white-space: nowrap; transition: color 0.35s; }}

  .card-body {{ font-size: 0.88rem; color: var(--card-body-color); line-height: 1.65; transition: color 0.35s; }}

  .transcript-badge {{
    display: inline-block;
    background: #6c47ff22;
    color: #6c47ff;
    border: 1px solid #6c47ff44;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 700;
    padding: 1px 7px;
    margin-left: 6px;
    vertical-align: middle;
  }}

  .card-source {{ display: flex; justify-content: flex-end; margin-top: 10px; }}

  .card-source a {{
    font-size: 0.78rem;
    font-weight: 300;
    color: #e03030 !important;
    text-decoration: none;
    letter-spacing: 0.1px;
    transition: opacity 0.15s;
  }}

  .card-source a:hover {{ opacity: 0.75; text-decoration: underline; }}

  .no-results {{
    text-align: center;
    padding: 60px 20px;
    color: var(--no-results-color);
    font-size: 1rem;
    font-weight: 600;
    opacity: 0.7;
  }}

  /* ── SCROLLBARS ── */
  main::-webkit-scrollbar {{ width: 6px; }}
  main::-webkit-scrollbar-track {{ background: transparent; }}
  main::-webkit-scrollbar-thumb {{ background: #c8bea0; border-radius: 10px; }}
  aside::-webkit-scrollbar {{ width: 4px; }}
  aside::-webkit-scrollbar-thumb {{ background: #c8bea0; border-radius: 10px; }}

  /* ── RESPONSIVE ── */
  @media (max-width: 768px) {{
    aside {{ width: 220px; padding: 18px 12px; }}
    main  {{ padding: 16px; }}
    header {{ padding: 0 16px; gap: 12px; }}
  }}

  @media (max-width: 580px) {{
    .layout {{ flex-direction: column; }}
    aside {{ width: 100%; height: auto; position: static; border-right: none; border-bottom: 1.5px solid #e0d5b8; min-height: unset; }}
    main {{ max-height: unset; }}
    .header-meta {{ display: none; }}
  }}
</style>
</head>
<body>

<!-- HEADER -->
<header>
  <a class="logo-area" href="#">
    {logo_tag}
  </a>
  <span class="header-meta">Généré le {generated} &bull; {count} articles</span>

  <div class="search-wrap">
    <input type="text" id="searchInput" placeholder="Rechercher dans les actualités…" autocomplete="off">
    <span class="search-icon">🔍</span>
  </div>

  <div class="theme-toggle">
    <span class="theme-icon">☀️</span>
    <div class="toggle-track" id="themeToggle">
      <div class="toggle-knob" id="themeKnob"></div>
    </div>
    <span class="theme-icon">🌙</span>
  </div>
</header>

<div class="layout">

  <!-- SIDEBAR -->
  <aside>

    <!-- Période -->
    <div class="sidebar-section">
      <h3>📅 Période :</h3>
      <div class="period-slider-wrap">
        <div class="slider-labels">
          <span>7 jours</span>
          <span>Aujourd'hui</span>
        </div>
        <input type="range" id="periodSlider" min="0" max="30" value="30" step="1">
        <div class="slider-value" id="sliderLabel">1 jour</div>
      </div>
    </div>

    <!-- Stats -->
    <div class="sidebar-section">
      <h3>📊 Résumé</h3>
      <div class="stats-row" id="statsRow"></div>
    </div>

    <!-- Rubriques -->
    <div class="sidebar-section">
      <h3>Rubriques :</h3>
      <div class="rubrique-grid" id="rubriquesGrid"></div>
    </div>

    <!-- Barème d'importance (Stars) -->
    <div class="sidebar-section">
      <h3>⭐ Importance :</h3>
      <div class="score-row" id="scoreRow"></div>
    </div>

    <!-- Langues -->
    <div class="sidebar-section" style="margin-top:auto;">
      <h3>🌐 Langue :</h3>
      <div class="langue-row" id="langueRow"></div>
    </div>

  </aside>

  <!-- FEED -->
  <main id="feed"></main>

</div>

<script>
/* ── PIPELINE DATA ── */
{js_data}

/* ── STATE ── */
const state = {{
  activeCategories: new Set(),
  activeScores: new Set(),
  search: '',
}};

/* ── Render Functions ── */
function renderStats() {{
  const row = document.getElementById('statsRow');
  const cats = {{}};
  ARTICLES.forEach(a => {{ cats[a.category] = (cats[a.category] || 0) + 1; }});
  row.innerHTML = '';
  Object.entries(cats).sort((a,b) => b[1]-a[1]).forEach(([cat, n]) => {{
    const chip = document.createElement('span');
    chip.className = 'stat-chip';
    chip.textContent = `${{cat}} ${{n}}`;
    row.appendChild(chip);
  }});
}}

function renderRubriques() {{
  const grid = document.getElementById('rubriquesGrid');
  const cats = [...new Set(ARTICLES.map(a => a.category))].sort();
  grid.innerHTML = '';
  cats.forEach(cat => {{
    const btn = document.createElement('button');
    btn.className = 'rubrique-btn' + (state.activeCategories.has(cat) ? ' active' : '');
    btn.textContent = (ARTICLES.find(a => a.category === cat)?.catEmoji || '🗞️') + ' ' + cat;
    btn.addEventListener('click', () => {{
      if (state.activeCategories.has(cat)) state.activeCategories.delete(cat);
      else state.activeCategories.add(cat);
      renderRubriques();
      renderFeed();
    }});
    grid.appendChild(btn);
  }});
}}

function renderScoreFilters() {{
  const row = document.getElementById('scoreRow');
  row.innerHTML = [5,4,3,2,1].map(n => {{
    const active = state.activeScores.has(n) ? ' active' : '';
    const label = '⭐'.repeat(n);
    return `<button class="score-btn freq-${{n===5?'viral':n===4?'une':n===3?'important':n===2?'modere':'minime'}}${{active}}" onclick="toggleScore(${{n}})">${{label}}</button>`;
  }}).join('');
}}

window.toggleScore = function(n) {{
  if (state.activeScores.has(n)) state.activeScores.delete(n);
  else state.activeScores.add(n);
  renderScoreFilters();
  renderFeed();
}}

function renderLangues() {{
  const row = document.getElementById('langueRow');
  row.innerHTML = `
    <button class="flag-btn active" onclick="setLang(this)"><img src="fr.png" alt="FR" width="20" height="20">Français</button>
    <button class="flag-btn" onclick="setLang(this)"><img src="us.png" alt="EN" width="20" height="20">English</button>
    <button class="flag-btn" onclick="setLang(this)"><img src="tn.png" alt="AR" width="20" height="20">العربية</button>
    
  `;
}}

window.setLang = function(btn) {{
  document.querySelectorAll('.flag-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  // TODO: Add language switching logic later
}};

function renderFeed() {{
  const feed = document.getElementById('feed');
  const search = state.search.toLowerCase();

  const filtered = ARTICLES.filter(a => {{
    if (state.activeCategories.size > 0 && !state.activeCategories.has(a.category)) return false;
    if (state.activeScores.size > 0 && !state.activeScores.has(a.score)) return false;
    if (search && !a.title.toLowerCase().includes(search) && !a.summary.toLowerCase().includes(search)) return false;
    return true;
  }});

  if (filtered.length === 0) {{
    feed.innerHTML = '<div class="no-results">Aucune actualité ne correspond à vos filtres.<br><br>🔄 Essayez de réinitialiser les filtres.</div>';
    return;
  }}

  feed.innerHTML = '';
  filtered.forEach((a, idx) => {{
    const transcriptBadge = a.transcript ? '<span class="transcript-badge">📝 Transcrit</span>' : '';
    const card = document.createElement('article');
    card.className = 'card';
    card.style.animationDelay = `${{idx * 0.04}}s`;
    card.innerHTML = `
      <div class="card-header">
        <span class="card-title">${{a.title}}${{transcriptBadge}}</span>
        <div class="card-tags">
          <span class="tag">${{a.catEmoji}} ${{a.category}}</span>
        </div>
        <div class="card-meta">
          <span class="freq-badge ${{a.freqCls}}">${{a.freqLbl}}</span>
          <span class="card-date">${{a.date}}</span>
        </div>
      </div>
      <div class="card-body">
        <p>${{a.summary}}</p>
        ${{a.impactScore > 1 || a.impactLabel ? `
        <div class="impact-row">
          <span class="impact-badge ${{a.impactCls}}">${{a.impactTxt}}</span>
          ${{a.impactLabel ? `<span class="impact-label">${{a.impactLabel}}</span>` : ''}}
        </div>` : ''}}
        <div class="card-source">
          <a href="${{a.link}}" target="_blank" rel="noopener">${{a.source}} &mdash; Lire &rarr;</a>
        </div>
      </div>
    `;
    feed.appendChild(card);
  }});
}}

/* ── SEARCH ── */
document.getElementById('searchInput').addEventListener('input', e => {{
  state.search = e.target.value;
  renderFeed();
}});

/* ── DARK MODE ── */
let dark = false;
document.getElementById('themeToggle').addEventListener('click', () => {{
  dark = !dark;
  document.body.classList.toggle('dark', dark);
  document.getElementById('themeKnob').style.left = dark ? '23px' : '3px';
}});

/* ── IMPACT FILTER ── */
function renderImpactFilters() {{
  const wrap = document.getElementById('impactRow');
  if (!wrap) return;
  const levels = [
    {{score:5, txt:'🔴 Critique',     cls:'impact-5'}},
    {{score:4, txt:'🟠 Important',    cls:'impact-4'}},
    {{score:3, txt:'🟡 À surveiller', cls:'impact-3'}},
    {{score:2, txt:'🔵 Faible',       cls:'impact-2'}},
    {{score:1, txt:'⚪ Neutre',       cls:'impact-1'}},
  ];
  const used = new Set(ARTICLES.map(a => a.impactScore));
  wrap.innerHTML = '';
  levels.filter(l => used.has(l.score)).forEach(l => {{
    const btn = document.createElement('button');
    btn.className = `score-btn ${{l.cls}}` + (state.activeImpacts.has(l.score) ? ' active' : '');
    btn.textContent = l.txt;
    btn.addEventListener('click', () => {{
      if (state.activeImpacts.has(l.score)) state.activeImpacts.delete(l.score);
      else state.activeImpacts.add(l.score);
      renderImpactFilters();
      renderFeed();
    }});
    wrap.appendChild(btn);
  }});
}}

/* ── INIT ── */
state.activeImpacts = new Set();
renderStats();
renderRubriques();
renderScoreFilters();
renderImpactFilters();
renderLangues();
renderFeed();
</script>
</body>
</html>"""


# ── Public API ────────────────────────────────────────────────────────────────

def build_report(articles: list) -> str:
    """Generates the Moojah HTML dashboard and writes it to OUTPUT_HTML."""
    html = _build_html(articles)
    path = OUTPUT_HTML
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"📄 Rapport Moojah généré : {path} ({len(articles)} articles)")
    return path


def open_report(path: str):
    """Opens the HTML report in the default browser."""
    abs_path = os.path.abspath(path)
    webbrowser.open(f"file://{abs_path}")
    print(f"🌐 Ouverture dans le navigateur : {abs_path}")


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test = [   ]
    path = build_report(test)
    open_report(path)