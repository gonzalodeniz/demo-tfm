#!/bin/bash

echo "🛑 PELIGRO: Estás a punto de DESTRUIR el stack completo."
echo "   1. Se borrarán TODOS los laboratorios de alumnos."
echo "   2. Se eliminarán las aplicaciones base: ArgoCD, Gitea, Checkmk y App-Edugitops."
echo "   3. Se perderán las configuraciones y datos no persistidos."
echo ""
read -p "¿Estás ABSOLUTAMENTE SEGURO de que quieres destruir todo el entorno? [y/N]: " confirm

if [[ ! "$confirm" =~ ^[yY]$ ]]; then
    echo "🚫 Operación cancelada. El entorno está a salvo."
    exit 0
fi

echo "🚀 Iniciando destrucción del entorno..."

# Llamamos al script de borrar laboratorios con el flag -f para no pedir confirmación de nuevo
./scripts/delete_labs.sh -f

echo "🔥 Destruyendo namespaces del stack base (argocd, gitea, checkmk, app-edugitops)..."
kubectl delete ns argocd gitea checkmk app-edugitops --ignore-not-found=true

echo "✅ Stack eliminado completamente."