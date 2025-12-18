#!/bin/bash
set -e

echo "🔄 Sincronizando laboratorios en ArgoCD..."

if [ -f .env ]; then
    set -a; source .env; set +a
fi

envsubst '$GITEA_REPO_URL $GITOPS_BASE_PATH $GITEA_BRANCH $GITEA_USER $GITEA_PASSWORD' < labs/applicationset.yaml | kubectl apply -f - -n argocd

echo "✅ Sincronización enviada."