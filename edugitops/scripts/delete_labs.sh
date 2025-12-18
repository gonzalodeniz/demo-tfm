#!/bin/bash

# Comprobamos si se pasa el argumento -f o --force para saltar la confirmación
FORCE=false
if [[ "$1" == "-f" || "$1" == "--force" ]]; then
    FORCE=true
fi

# Si no es forzado, pedimos confirmación
if [ "$FORCE" = false ]; then
    echo "⚠️  ATENCIÓN: Estás a punto de borrar TODOS los laboratorios de los alumnos."
    echo "   - Se eliminará el ApplicationSet 'alumnos-apps' en ArgoCD."
    echo "   - Se borrarán todos los namespaces que comiencen por 'alumno-'."
    echo ""
    read -p "¿Estás SEGURO de que quieres continuar? [y/N]: " confirm
    
    # Si la respuesta no es y o Y, salimos
    if [[ ! "$confirm" =~ ^[yY]$ ]]; then
        echo "🚫 Operación cancelada por el usuario."
        exit 0
    fi
fi

echo "🗑️  Eliminando ApplicationSet..."
kubectl delete -f labs/applicationset.yaml -n argocd --ignore-not-found=true

echo "🧹 Buscando namespaces de alumnos ('alumno-*')..."

NAMESPACES=$(kubectl get ns -o jsonpath="{.items[*].metadata.name}" | tr ' ' '\n' | grep "^alumno-")

if [ -z "$NAMESPACES" ]; then
    echo "   -> No se encontraron namespaces de alumnos."
else
    for ns in $NAMESPACES; do
        echo "   -> Borrando namespace: $ns..."
        kubectl delete ns $ns --ignore-not-found=true &
    done
    wait # Esperar a que terminen los borrados en segundo plano
fi

echo "✅ Limpieza de alumnos completada."