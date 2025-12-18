#!/bin/bash

echo "🔑 Credenciales del Sistema:"
echo ""
echo "--- ArgoCD ---"
echo "User: admin"
PASS=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "No encontrado")
echo "Pass: $PASS"
echo ""

if [ -f .env ]; then
    set -a; source .env; set +a
    echo "--- Gitea (desde .env) ---"
    echo "User: $GITEA_USER"
    echo "Pass: $GITEA_PASSWORD"
    echo ""
    echo "--- Checkmk (desde .env) ---"
    echo "User: $CHECKMK_API_USER"
    echo "Pass: $CHECKMK_API_SECRET"
else
    echo "⚠️  No se pudo leer el fichero .env para Gitea/Checkmk"
fi