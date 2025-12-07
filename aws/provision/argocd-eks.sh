#!/bin/bash

# Detener el script si ocurre algún error
set -e

NAMESPACE="argocd"
URL_MANIFEST="https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"

echo "=================================================="
echo "🚀 Iniciando instalación de ArgoCD en EKS"
echo "=================================================="

# 1. Crear el Namespace (si no existe)
echo "[1/5] Verificando namespace '$NAMESPACE'..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# 2. Instalar ArgoCD desde el repositorio oficial
echo "[2/5] Aplicando manifiestos oficiales..."
kubectl apply -n $NAMESPACE -f $URL_MANIFEST

# 3. Parchear el servicio para usar LoadBalancer
# Esta es la forma más limpia de modificar un manifiesto externo sin editar el archivo.
echo "[3/5] Configurando Service como LoadBalancer..."
kubectl patch svc argocd-server -n $NAMESPACE -p '{"spec": {"type": "LoadBalancer"}}'

# (Opcional) Si prefieres un Network Load Balancer (NLB) de AWS en lugar del Classic,
# descomenta la siguiente línea:
# kubectl annotate svc argocd-server -n $NAMESPACE service.beta.kubernetes.io/aws-load-balancer-type="nlb" --overwrite

# 4. Esperar a que el Load Balancer tenga una IP/Hostname asignado
echo "[4/5] Esperando a que AWS provisione el Load Balancer (esto puede tardar unos minutos)..."
until kubectl get svc argocd-server -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' &> /dev/null
do
    printf "."
    sleep 5
done
echo ""
LB_HOSTNAME=$(kubectl get svc argocd-server -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# 5. Obtener la contraseña inicial de admin
echo "[5/5] Recuperando credenciales iniciales..."
# Esperar a que el secret esté disponible
sleep 2
ADMIN_PASSWORD=$(kubectl -n $NAMESPACE get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

sleep 5
echo ""
echo "=================================================="
echo "✅ Instalación completada con éxito"
echo "=================================================="
echo ""
echo "📂 Acceso a la UI:"
echo "   URL: https://$LB_HOSTNAME"
echo ""
echo "🔑 Credenciales:"
echo "   Usuario: admin"
echo "   Password: $ADMIN_PASSWORD"
echo ""
echo "⚠️ Nota: El DNS de AWS puede tardar unos minutos en propagarse."
echo ""
echo " Para visualizar la URL del Load Balancer en cualquier momento, ejecuta:"
echo "   kubectl get svc -n argocd|grep LoadBalancer"
echo "=================================================="