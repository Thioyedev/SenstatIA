# Déploiement sur Hetzner — SenStat

Durée estimée : **20–30 minutes** (hors téléchargement du modèle d'embeddings ~2.1 GB)

---

## Étape 1 — Créer le serveur Hetzner

1. Créez un compte sur [hetzner.com](https://www.hetzner.com)
2. Dans la console Cloud → **New Project** → nommez-le `senstat`
3. Cliquez **Add Server** avec ces paramètres :

| Paramètre | Valeur |
|---|---|
| Location | Nuremberg ou Helsinki |
| Image | **Ubuntu 24.04** |
| Type | **CX31** (2 vCPU, 8 GB RAM) — €8.90/mo |
| SSH Key | Ajoutez votre clé publique (`~/.ssh/id_rsa.pub`) |
| Name | `senstat-prod` |

4. Cliquez **Create & Buy** → notez l'adresse IP du serveur

> Si vous n'avez pas de clé SSH : `ssh-keygen -t ed25519 -C "senstat"` puis copiez le contenu de `~/.ssh/id_ed25519.pub`

---

## Étape 2 — Configurer le serveur

Connectez-vous :
```bash
ssh root@VOTRE_IP
```

Téléchargez et exécutez le script de configuration :
```bash
curl -fsSL https://raw.githubusercontent.com/SenStat/Senstat-Agent/dev/scripts/server_setup.sh | bash
```

Ce script installe : Docker, Docker Compose, Git, UFW (firewall), et ajoute 4 GB de swap.

---

## Étape 3 — Cloner le projet

```bash
cd /app
git clone https://github.com/SenStat/Senstat-Agent.git .
git checkout dev
```

---

## Étape 4 — Uploader la base vectorielle (ChromaDB)

**Depuis votre machine locale**, uploadez le dossier `data/chroma/` (21 MB) :

```bash
scp -r "data/chroma" root@VOTRE_IP:/app/data/
```

Vérifiez sur le serveur :
```bash
ls /app/data/chroma/
# doit afficher : chroma.sqlite3  db.../
```

---

## Étape 5 — Configurer les variables d'environnement

Sur le serveur :
```bash
cp .env.example .env
nano .env
```

Renseignez au minimum :
```env
ANTHROPIC_API_KEY=sk-ant-...
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=intfloat/multilingual-e5-large
EMBEDDING_DEVICE=cpu
DATA_RAW_DIR=./data/raw
DATA_PROCESSED_DIR=./data/processed
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

Sauvegardez : `Ctrl+O` puis `Ctrl+X`

---

## Étape 6 — Déployer

```bash
bash scripts/deploy.sh
```

Ce script :
1. Vérifie `.env` et `data/chroma/`
2. Build les images Docker (~5–10 min au premier lancement)
3. Démarre les 4 containers (api, frontend-pro, frontend-public, nginx)
4. Attend que l'API soit healthy (le modèle d'embeddings se télécharge ~2.1 GB, ~60s)
5. Affiche les URLs de votre application

---

## Résultat

| URL | Interface |
|---|---|
| `http://VOTRE_IP` | Grand Public |
| `http://VOTRE_IP/pro` | Interface Pro |
| `http://VOTRE_IP/api/health` | Santé de l'API |

---

## Commandes utiles

```bash
# Voir les logs en temps réel
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f api
docker compose logs -f frontend-public

# Statut des containers
docker compose ps

# Redémarrer un service
docker compose restart api

# Arrêter tout
docker compose down

# Mettre à jour l'application (après un git push)
git pull
docker compose build
docker compose up -d
```

---

## Mise à jour de l'application

Chaque fois que vous poussez du code sur `dev` :

```bash
# Sur le serveur
cd /app
git pull
docker compose up -d --build
```

---

## Ajouter un nom de domaine (optionnel)

1. Achetez un domaine (ex: `senstat.sn`) et pointez son DNS vers votre IP Hetzner :
   ```
   A  @      VOTRE_IP
   A  www    VOTRE_IP
   ```

2. Installez Certbot pour HTTPS :
   ```bash
   apt install certbot python3-certbot-nginx -y
   certbot --nginx -d senstat.sn -d www.senstat.sn
   ```

3. Certbot modifie automatiquement la config Nginx pour ajouter HTTPS.

---

## Surveillance

```bash
# Utilisation mémoire / CPU
htop

# Espace disque
df -h

# Utilisation par container
docker stats
```

> Le modèle d'embeddings (2.1 GB) est téléchargé une seule fois et persisté dans un volume Docker (`model_cache`). Les redémarrages suivants sont rapides (~10s).
