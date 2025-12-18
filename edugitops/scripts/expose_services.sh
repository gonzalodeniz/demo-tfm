#!/bin/bash
set -e

echo "🌐 Exponiendo servicios en segundo plano..."
echo "Logs disponibles en /tmp/port-forward-*.log"

nohup kubectl port-forward -n gitea svc/gitea 3000:80 >/tmp/port-forward-gitea.log 2>&1 & echo $! >/tmp/port-forward-gitea.pid
nohup kubectl port-forward -n checkmk svc/checkmk 5000:80 6557:6557 >/tmp/port-forward-checkmk.log 2>&1 & echo $! >/tmp/port-forward-checkmk.pid
nohup kubectl port-forward -n argocd svc/argocd-server 8080:443 >/tmp/port-forward-argocd.log 2>&1 & echo $! >/tmp/port-forward-argocd.pid
nohup kubectl port-forward -n app-edugitops svc/app-edugitops 5001:5001 >/tmp/port-forward-edugitops.log 2>&1 & echo $! >/tmp/port-forward-edugitops.pid

echo "✅ Servicios expuestos:"
echo "  - Gitea:        http://localhost:3000/"
echo "  - Checkmk:      http://localhost:5000/"
echo "  - ArgoCD:       http://localhost:8080/"
echo "  - App Edugitops: http://localhost:5001/"
echo ""
echo "Para detenerlos ejecuta:"
echo "kill \$(cat /tmp/port-forward-gitea.pid) \$(cat /tmp/port-forward-checkmk.pid) \$(cat /tmp/port-forward-argocd.pid) \$(cat /tmp/port-forward-edugitops.pid)"