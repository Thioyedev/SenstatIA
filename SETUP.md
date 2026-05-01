# Guide d'installation — SenStat

Ce guide est destiné aux collaborateurs qui rejoignent le projet.

---

## Prérequis système

| Outil | Version | Installation |
|---|---|---|
| Python | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Git | any | [git-scm.com](https://git-scm.com/) |
| poppler | any | `brew install poppler` (macOS) / `apt install poppler-utils` (Linux) |
| tesseract | any | `brew install tesseract` (macOS) / `apt install tesseract-ocr` (Linux) |

> poppler et tesseract sont nécessaires uniquement si vous relancez l'ingestion (Option A ci-dessous).

---

## 1. Cloner le dépôt

```bash
git clone https://github.com/SenStat/Senstat-Agent.git
cd Senstat-Agent
git checkout dev
```

---

## 2. Environnement Python

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

pip install -e .
```

---

## 3. Variables d'environnement

```bash
cp .env.example .env
```

Ouvrez `.env` et renseignez au minimum :

```env
ANTHROPIC_API_KEY=sk-ant-...        # obligatoire — demandez la clé au lead
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DEVICE=cpu
DATA_RAW_DIR=./data/raw
DATA_PROCESSED_DIR=./data/processed
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

> Ne commitez jamais le fichier `.env` — il est dans `.gitignore`.

---

## 4. Base vectorielle (ChromaDB)

Choisissez l'une des deux options :

### Option A — Recevoir le dossier `data/chroma/` (recommandé, plus rapide)

Demandez au lead le dossier `data/chroma/` (21 Mo, partagé via Drive ou WeTransfer).  
Placez-le à la racine du projet :

```
Senstat-Agent/
└── data/
    └── chroma/          ← dossier reçu, à placer ici
        ├── chroma.sqlite3
        └── db.../
```

Vérifiez que tout est en ordre :

```bash
python -c "from vectorstore.chroma_store import ChromaStore; s = ChromaStore(); print(s.collection.count(), 'chunks')"
```

Sortie attendue : `1887 chunks`

---

### Option B — Relancer l'ingestion vous-même

Téléchargez les 4 rapports PDF depuis [ansd.sn](https://www.ansd.sn) et placez-les dans `data/raw/` avec ces noms exacts :

```
data/raw/
├── EHCVM_2021_2022.pdf
├── RGPH5_economie_2024.pdf
├── RGPH5_preliminaire_2023.pdf
└── SES_2022_2023.pdf
```

Lancez l'ingestion (environ 5–10 minutes) :

```bash
python -m ingestion.pipeline
```

Vérifiez :

```bash
python -c "from vectorstore.chroma_store import ChromaStore; s = ChromaStore(); print(s.collection.count(), 'chunks')"
```

Sortie attendue : `1887 chunks`

---

## 5. Lancer l'application

Ouvrez **3 terminaux** depuis la racine du projet (venv activé dans chacun).

### Terminal 1 — API FastAPI

```bash
uvicorn api.main:app --reload --port 8000
```

Vérification :
```bash
curl http://localhost:8000/health
```

### Terminal 2 — Frontend Pro

```bash
streamlit run "frontend/🏠_Accueil.py" --server.port 8501
```

Ouvrez [http://localhost:8501](http://localhost:8501)

### Terminal 3 — Frontend Grand Public

```bash
streamlit run "frontend_public/🏠_Accueil.py" --server.port 8502
```

Ouvrez [http://localhost:8502](http://localhost:8502)

---

## 6. Tester que tout fonctionne

```bash
# Test de l'API
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Quel est le taux de pauvreté au Sénégal en 2021 ?"}'
```

La réponse doit contenir une citation `[ANSD — EHCVM 2021-2022, p.XX]`.

---

## 7. Lancer l'évaluation (optionnel)

```bash
# Évaluation rapide (sans RAGAS)
python scripts/eval_retrieval.py --no-ragas --n 5

# Évaluation complète
python scripts/eval_retrieval.py
```

---

## Structure des branches

| Branche | Usage |
|---|---|
| `main` | Production stable |
| `dev` | Développement actif — travaillez ici |

Créez vos branches depuis `dev` :

```bash
git checkout dev
git checkout -b feature/ma-fonctionnalite
```

---

## Problèmes courants

**`ModuleNotFoundError`**
```bash
# Vérifiez que le venv est activé
source venv/bin/activate
pip install -e .
```

**`0 chunks` après ingestion**
```bash
# Vérifiez les noms de fichiers dans data/raw/
ls data/raw/
# Doivent correspondre exactement aux noms dans ingestion/pipeline.py
```

**`ANTHROPIC_API_KEY not found`**
```bash
# Vérifiez que .env existe et contient la clé
cat .env | grep ANTHROPIC
```

**Port déjà utilisé**
```bash
# Changez le port
uvicorn api.main:app --port 8001
streamlit run "frontend/🏠_Accueil.py" --server.port 8503
```

---

## Contact

Pour toute question, contactez le lead du projet.
