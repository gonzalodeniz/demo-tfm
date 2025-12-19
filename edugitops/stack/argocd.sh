#!/bin/bash

# Detener ante cualquier error
set -e

NAMESPACE="argocd"
URL_MANIFEST="https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"

echo "=================================================="
echo "🚀 Iniciando instalación de ArgoCD (Con Parches Anti-Reinicios)"
echo "=================================================="

# --- 1. DETECCIÓN DE ENTORNO ---
if kubectl get node minikube &> /dev/null; then
    ENV_TYPE="MINIKUBE"
    echo "📍 Entorno detectado: MINIKUBE (Local)"
else
    ENV_TYPE="EKS"
    echo "📍 Entorno detectado: EKS / AWS (Nube)"
fi

# --- 2. INSTALACIÓN ---
echo "[1/5] Creando namespace '$NAMESPACE'..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo "[2/5] Aplicando manifiestos oficiales..."
kubectl apply -n $NAMESPACE -f $URL_MANIFEST

# --- 3. PARCHEO DE PROBES (SOLUCIÓN A LOS REINICIOS) ---
echo "[3/5] Aplicando parches de estabilidad (Timeout y Liveness)..."

# Parche 1: ArgoCD SERVER (La interfaz web)
# Aumentamos el timeout y el delay inicial para evitar que se reinicie al arrancar
kubectl -n $NAMESPACE patch deploy argocd-server --type='json' -p='[
  {"op": "replace", "path": "/spec/template/spec/containers/0/livenessProbe/initialDelaySeconds", "value": 180},
  {"op": "replace", "path": "/spec/template/spec/containers/0/livenessProbe/timeoutSeconds", "value": 15},
  {"op": "replace", "path": "/spec/template/spec/containers/0/livenessProbe/failureThreshold", "value": 10},
  {"op": "replace", "path": "/spec/template/spec/containers/0/readinessProbe/initialDelaySeconds", "value": 60},
  {"op": "replace", "path": "/spec/template/spec/containers/0/readinessProbe/timeoutSeconds", "value": 15}
]' || echo "⚠️ Advertencia: No se pudo parchear argocd-server"

# Parche 2: ArgoCD REPO SERVER (El backend que clona git)
# Este es el que te estaba fallando con "Error 143/137"
kubectl -n $NAMESPACE patch deploy argocd-repo-server --type='json' -p='[
  {"op": "replace", "path": "/spec/template/spec/containers/0/livenessProbe/initialDelaySeconds", "value": 180},
  {"op": "replace", "path": "/spec/template/spec/containers/0/livenessProbe/timeoutSeconds", "value": 15},
  {"op": "replace", "path": "/spec/template/spec/containers/0/livenessProbe/failureThreshold", "value": 10},
  {"op": "replace", "path": "/spec/template/spec/containers/0/readinessProbe/initialDelaySeconds", "value": 60},
  {"op": "replace", "path": "/spec/template/spec/containers/0/readinessProbe/timeoutSeconds", "value": 15}
]' || echo "⚠️ Advertencia: No se pudo parchear argocd-repo-server"

# --- 4. CONFIGURACIÓN DEL SERVICIO ---
echo "[4/5] Configurando Service como NodePort..."
# Usamos NodePort siempre. Es más seguro en AWS Academy para evitar problemas de cuota de ELB
# y funciona igual en Minikube con port-forward.
kubectl patch svc argocd-server -n $NAMESPACE -p '{"spec": {"type": "NodePort"}}'
UI_URL="https://localhost:8080 (Requiere 'make expose')"

# --- 5. CREDENCIALES ---
echo "[5/5] Esperando a que el secret de admin esté disponible..."
sleep 5
until kubectl -n $NAMESPACE get secret argocd-initial-admin-secret &> /dev/null; do
    echo "      Esperando creación de secretos..."
    sleep 5
done

ADMIN_PASSWORD=$(kubectl -n $NAMESPACE get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

echo ""
echo "=================================================="
echo "✅ Instalación completada y parcheada"
echo "=================================================="
echo "🌍 Entorno: $ENV_TYPE"
echo "📂 UI ArgoCD: $UI_URL"
echo "👤 Usuario:   admin"
echo "🔑 Password:  $ADMIN_PASSWORD"
echo "=================================================="