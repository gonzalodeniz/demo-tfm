#!/bin/bash

# Detener ante cualquier error
set -e

NAMESPACE="argocd"
URL_MANIFEST="https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"

echo "=================================================="
echo "🚀 Iniciando instalación de ArgoCD (Modo Híbrido)"
echo "=================================================="

# --- 1. DETECCIÓN DE ENTORNO ---
# Comprobamos si el contexto actual o los nodos indican que es Minikube
if kubectl get node minikube &> /dev/null; then
    ENV_TYPE="MINIKUBE"
    echo "📍 Entorno detectado: MINIKUBE (Local)"
else
    ENV_TYPE="EKS"
    echo "📍 Entorno detectado: EKS / AWS (Nube)"
fi

# --- 2. INSTALACIÓN ---
echo "[1/4] Creando namespace '$NAMESPACE'..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo "[2/4] Aplicando manifiestos oficiales..."
kubectl apply -n $NAMESPACE -f $URL_MANIFEST

# --- 3. CONFIGURACIÓN DEL SERVICIO ---
if [ "$ENV_TYPE" = "EKS" ]; then
    echo "[3/4] [EKS] Configurando Service como LoadBalancer..."
    kubectl patch svc argocd-server -n $NAMESPACE -p '{"spec": {"type": "LoadBalancer"}}'
    
    echo "      Esperando a que AWS asigne el Hostname del LoadBalancer (puede tardar)..."
    until kubectl get svc argocd-server -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' &> /dev/null
    do
        printf "."
        sleep 5
    done
    echo ""
    LB_HOST=$(kubectl get svc argocd-server -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    UI_URL="https://$LB_HOST"
else
    echo "[3/4] [MINIKUBE] Configurando Service como NodePort..."
    # Usamos NodePort para facilitar acceso si falla el port-forward, aunque el Makefile usa port-forward.
    kubectl patch svc argocd-server -n $NAMESPACE -p '{"spec": {"type": "NodePort"}}'
    UI_URL="https://localhost:8080 (Requiere 'make expose' o port-forward)"
fi

# --- 4. CREDENCIALES ---
echo "[4/4] Esperando a que el secret de admin esté disponible..."
# Esperamos un poco a que el secret se genere tras el despliegue
sleep 5
until kubectl -n $NAMESPACE get secret argocd-initial-admin-secret &> /dev/null; do
    echo "      Esperando creación de secretos..."
    sleep 5
done

ADMIN_PASSWORD=$(kubectl -n $NAMESPACE get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

echo ""
echo "=================================================="
echo "✅ Instalación completada"
echo "=================================================="
echo "🌍 Entorno: $ENV_TYPE"
echo "📂 UI ArgoCD: $UI_URL"
echo "👤 Usuario:   admin"
echo "🔑 Password:  $ADMIN_PASSWORD"
echo "=================================================="