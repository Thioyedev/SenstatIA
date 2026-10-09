# SenstatIA — Staging

> **ChatGPT vous donne un chiffre. SenStat vous donne le chiffre officiel, avec la source, le rapport et la page.**

**Branche :** `stg` — environnement de staging déployé sur Hetzner

---

## Environnement déployé

| | |
|---|---|
| **Serveur** | Hetzner CX31 — Ubuntu 24.04 |
| **IP** | `65.109.143.85` |
| **Stack** | Docker Compose (nginx + api + 2 frontends) |

| Interface | URL |
|---|---|
| Grand Public | http://65.109.143.85 |
| Interface Pro | http://65.109.143.85/pro |
| API health | http://65.109.143.85/api/health |
| API docs | http://65.109.143.85/api/docs |

---

## État du déploiement

| Métrique | Valeur |
|---|---|
| Chunks indexés | **7 571** |
| Sources actives | **10 / 25** |
| Phase déployée | **Phase 2 — Multi-Agents** |
| Modèle routing | `claude-haiku-4-5` |
| Modèle synthesis | `claude-sonnet-4-20250514` |
| Embeddings | `intfloat/multilingual-e5-large` |
| Vector store | ChromaDB (local persisté) |

---

## Architecture déployée

```
Internet
    │
    ▼
nginx :80
    ├── /          → Streamlit Public  :8501
    ├── /pro       → Streamlit Pro     :8502
    └── /api/      → FastAPI           :8000
                        │
                        ▼
                   LangGraph StateGraph
                        │
                   ┌────┴────────────────────┐
                   Router (Haiku)            │
                   Retrieval (e5 + BM25 + CE)│
                   Trend / Compare (Haiku)   │
                   Synthesis (Sonnet)        │
                   └─────────────────────────┘
                        │
                   ChromaDB (./data/chroma)
```

---

## Mettre à jour le staging

### Depuis la branche `dev` (promotion standard)

```bash
# 1. Merger dev → stg en local
git checkout stg
git merge dev
git push origin stg

# 2. Sur le serveur Hetzner
ssh root@65.109.143.85
cd /app
git pull origin stg
docker compose build api
docker compose up -d
```

### Si la base vectorielle a changé (nouvelle ingestion)

```bash
# Depuis la machine locale après ingestion
rsync -avz data/chroma/ root@65.109.143.85:/app/data/chroma/

# Sur le serveur — l'API tourne sous l'UID 10001 et doit pouvoir écrire dans l'index
chown -R 10001:10001 /app/data/chroma
docker restart senstat-api
```

### Vérification post-déploiement

```bash
curl http://65.109.143.85/api/health
# → {"status":"ok","chunks_indexed":7571}
```

---

## Commandes serveur

```bash
ssh root@65.109.143.85
cd /app

# Statut des containers
docker compose ps

# Logs en temps réel
docker compose logs -f
docker compose logs -f api

# Redémarrer un service
docker compose restart api

# Ressources
docker stats
htop
df -h
```

---

## Tester le staging

```bash
# Vérification santé
curl http://65.109.143.85/api/health

# Requête de test
curl -X POST http://65.109.143.85/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Quel est le taux de pauvreté au Sénégal en 2021 ?"}'

# Liste des sources indexées
curl http://65.109.143.85/api/documents
```

**Scénarios de validation :**

| Question | Intent attendu | Comportement attendu |
|---|---|---|
| "Quel est le taux de pauvreté en 2021 ?" | `lookup` | Réponse + citation EHCVM |
| "Évolution du PIB depuis 2015 ?" | `trend` | Réponse + série temporelle |
| "Compare chômage Dakar vs Ziguinchor" | `compare` | Réponse comparative |
| "Taux de criminalité ?" | `lookup` | Refus (hors corpus) |

---

## Promouvoir stg → main

Quand le staging est validé :

```bash
# En local
git checkout main
git merge stg
git push origin main
```

> **Règle :** merge `stg → main` uniquement après validation manuelle sur http://65.109.143.85.

---

## Git Branching

```
feature/* ──┐
fix/*       ├──► dev ──► stg ──► main
docs/*      │
chore/*   ──┘

hotfix/* ──► main ──► (backport) ──► dev
```

`stg` reçoit uniquement des PR/merges depuis `dev`. Aucun développement direct sur `stg`.

---

## Documentation

| Fichier | Contenu |
|---|---|
| `ARCHITECTURE.md` | Architecture complète, agents, retrieval, infra |
| `CLAUDE.md` | Guide développeur, git branching, phases |
| `DEPLOY.md` | Déploiement Hetzner pas à pas |

---

## Licence

MIT — Données issues de sources officielles publiques (ANSD, DPEE, BCEAO, IMF, World Bank).

*Phase 2 déployée · Mai 2026*
