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

## Déploiement automatique du staging (CI)

Le job `deploy-staging` de `.github/workflows/ci.yml` déploie chaque push sur
`stg`, une fois lint, tests et build Docker passés. Il se connecte en SSH et
envoie `deploy <sha>` ; côté serveur, `scripts/deploy_ci.sh` fait avancer
`/app` jusqu'à ce commit (fast-forward uniquement), reconstruit les conteneurs
et attend que `/health` réponde `ok` avec un index non vide.

Le job reste **ignoré** tant que la variable `STAGING_DEPLOY_ENABLED` ne vaut
pas `true`. Mise en place, une seule fois :

**1. Clé dédiée** (sur votre machine) :

```bash
ssh-keygen -t ed25519 -f ~/.ssh/senstat_deploy -N "" -C senstat-ci-deploy
```

**2. Script et clé sur le serveur.** Le script est installé **hors de `/app`** :
un push sur `stg` ne peut ainsi pas modifier ce qui s'exécute en root.
Relancer `install` après chaque modification de `scripts/deploy_ci.sh`.

```bash
ssh root@65.109.143.85
cd /app && git status   # doit être sur stg, sans modification locale
install -m 755 /app/scripts/deploy_ci.sh /usr/local/bin/senstat-deploy
```

Puis ajouter **une ligne** à `/root/.ssh/authorized_keys` (la clé publique est
dans `~/.ssh/senstat_deploy.pub`). Les options limitent cette clé au seul script :

```
command="/usr/local/bin/senstat-deploy",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAA... senstat-ci-deploy
```

**3. Empreinte du serveur.** Récupérer la clé d'hôte, puis vérifier que son
empreinte correspond à celle affichée **sur le serveur** :

```bash
ssh-keyscan -t ed25519 65.109.143.85 > /tmp/staging_known_hosts
ssh-keygen -lf /tmp/staging_known_hosts                       # sur votre machine
ssh root@65.109.143.85 ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub   # doit être identique
```

**4. Secrets et activation** :

```bash
gh secret set STAGING_SSH_KEY < ~/.ssh/senstat_deploy
gh secret set STAGING_KNOWN_HOSTS < /tmp/staging_known_hosts
gh variable set STAGING_DEPLOY_ENABLED --body true
```

**Tester la clé avant d'activer** : `ssh -i ~/.ssh/senstat_deploy root@65.109.143.85 "deploy $(git rev-parse SenStat/stg)"`
doit déployer ; toute autre commande doit répondre `usage: deploy <40-char commit sha>`.

Le déploiement échoue (job rouge, conteneurs précédents inchangés si le build
échoue) si `.env` ou `data/chroma` manquent, si `/app` n'est pas sur `stg` ou a
divergé, ou si l'API n'est pas saine après 10 minutes. L'index Chroma n'est pas
dans git : il se met toujours à jour à la main (`rsync`, voir README).

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
