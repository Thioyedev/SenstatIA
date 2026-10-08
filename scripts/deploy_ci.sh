#!/usr/bin/env bash
# deploy_ci.sh — staging deploy, triggered by GitHub Actions over SSH.
#
# Installed once, by hand, OUTSIDE the repo checkout:
#
#   install -m 755 /app/scripts/deploy_ci.sh /usr/local/bin/senstat-deploy
#
# and set as the forced command of the CI deploy key in authorized_keys, so
# that key can run this script and nothing else:
#
#   command="/usr/local/bin/senstat-deploy",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAA... senstat-ci-deploy
#
# Running it from outside /app means a push to stg cannot change what runs as
# root here, and the script is never rewritten by the git update it performs.
# Re-run the install command after changing this file.
#
# The workflow sends "deploy <sha>", which sshd exposes as $SSH_ORIGINAL_COMMAND.
# Only that commit (the one that passed CI) is deployed, and only as a
# fast-forward: a checkout that has diverged from stg stops the deploy instead
# of being overwritten.
set -euo pipefail

APP_DIR=/app
REPO_URL=https://github.com/Thioyedev/SenstatIA.git
BRANCH=stg
HEALTH_URL=http://localhost:8000/health
HEALTH_TIMEOUT=600 # first start downloads the embedding model (~2 GB)

fail() {
    echo "❌ $*" >&2
    exit 1
}

main() {
    local action sha extra
    read -r action sha extra <<<"${SSH_ORIGINAL_COMMAND:-}"
    if [[ "$action" != "deploy" || ! "$sha" =~ ^[0-9a-f]{40}$ || -n "$extra" ]]; then
        echo "usage: deploy <40-char commit sha>" >&2
        exit 2
    fi

    exec 9>/var/lock/senstat-deploy.lock
    flock -n 9 || fail "another deploy is already running"

    cd "$APP_DIR"
    [[ -f .env ]] || fail ".env missing in $APP_DIR"
    [[ -f data/chroma/chroma.sqlite3 ]] || fail "data/chroma is empty — rsync the index first"
    [[ "$(git rev-parse --abbrev-ref HEAD)" == "$BRANCH" ]] || fail "checkout is not on $BRANCH"

    echo "▶ Fetching $BRANCH"
    git fetch --quiet "$REPO_URL" "$BRANCH"
    git merge-base --is-ancestor "$sha" FETCH_HEAD || fail "$sha is not on $BRANCH"
    git merge --ff-only "$sha"

    echo "▶ Building and restarting containers"
    docker compose up -d --build
    docker image prune -f >/dev/null

    echo "▶ Waiting for the API (up to ${HEALTH_TIMEOUT}s)"
    local deadline=$((SECONDS + HEALTH_TIMEOUT)) body=""
    until body=$(curl -fsS -m 5 "$HEALTH_URL" 2>/dev/null) && grep -q '"status":"ok"' <<<"$body"; do
        if ((SECONDS >= deadline)); then
            docker compose ps
            docker compose logs --tail 50 api
            fail "API not healthy after ${HEALTH_TIMEOUT}s"
        fi
        sleep 10
    done
    # "ok" only means Chroma answered; an empty collection still reports ok.
    if grep -q '"chunks_indexed":0[,}]' <<<"$body"; then
        fail "API is up but the index is empty: $body"
    fi

    echo "✓ Deployed $sha — $body"
}

main "$@"
