# 🇹🇳 Agent d'Actualités Tunisiennes

Agent Python qui agrège les actualités tendance de sources tunisiennes et mondiales,
les résume en **français** grâce à l'IA (Google Gemini), et génère un rapport HTML local.

---

## 📦 Sources de données

| Source | Type | Langue |
|---|---|---|
| Google Trends | Tendances de recherche | TN |
| Al Wataniya (YouTube) | Vidéos tendance | AR/FR |
| Tunis Afrique Presse | RSS | FR |
| Tunisie Numérique | RSS | FR |
| Mosaïque FM | RSS | FR |
| Jawhara FM | RSS | FR |
| Business News TN | RSS | FR |

---

## 🗂️ Structure du projet

```
news_agent/
├── .env.example       ← Modèle pour vos clés API
├── .env               ← Vos clés API (à créer, ne pas partager)
├── requirements.txt   ← Dépendances Python
├── config.py          ← Configuration centralisée (sources, modèles)
├── fetcher.py         ← Récupère les articles depuis toutes les sources
├── summarizer.py      ← Résume chaque article avec Gemini
├── reporter.py        ← Génère le rapport HTML
└── main.py            ← Point d'entrée (lancement manuel)
```

---

## ⚙️ Installation

### 1. Cloner / copier le projet
```bash
cd news_agent
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configurer les clés API
```bash
cp .env.example .env
```
Ouvrez `.env` et renseignez vos deux clés :

| Clé | Où l'obtenir | Gratuit ? |
|---|---|---|
| `GROK_API_KEY` | [console.groq.com](https://console.groq.com/keys) | ✅ Oui |
| `YOUTUBE_API_KEY` | [console.cloud.google.com](https://console.cloud.google.com) → YouTube Data API v3 | ✅ Oui |

---

## 🚀 Utilisation

```bash
python main.py
```

Le script va :
1. Récupérer les tendances depuis toutes les sources
2. Résumer chaque article en français avec Gemini
3. Générer `trends_report.html` dans le dossier courant
4. Ouvrir automatiquement le rapport dans votre navigateur

---

## 📝 Notes

- Le rapport est généré **à la demande** (pas de tâche automatique).
- Les flux RSS sont publics et ne nécessitent pas de clé API.
