# Nombre del contexto EKS (ajústalo si es distinto en tu kubeconfig)
EKS_CONTEXT = arn:aws:eks:us-east-1:202974436470:cluster/cluster-tfm
MINIKUBE_CONTEXT = minikube

.PHONY: help use-minikube use-eks list-contexts current-context argocd gitea gitea-init checkmk stack sincro delete passwords start-minikube expose

help:
	@echo ""
	@echo "Opciones disponibles:"
	@echo ""
	@echo "  make help             - Muestra esta ayuda"
	@echo ""
	@echo "Gestión de contextos de kubectl"
	@echo "------------------------"	
	@echo "  make list-contexts    - Lista todos los contextos disponibles en kubectl"
	@echo "  make current-context  - Muestra el contexto actual de kubectl"
	@echo "  make use-minikube     - Cambia el contexto de kubectl a Minikube"
	@echo "  make use-eks          - Cambia el contexto de kubectl al clúster EKS"
	@echo ""
	@echo "Despliegues del stack"
	@echo "------------------------"
	@echo "  make argocd           - Despliega ArgoCD"
	@echo "  make gitea            - Despliega Gitea"
	@echo "  make gitea-init       - Inicializa repositorio git (después de exponer servicios)"
	@echo "  make checkmk          - Despliega Checkmk"
	@echo "  make app-edugitops    - Despliega app-edugitops"
	@echo "  make stack            - Despliega el stack completo"
	@echo ""
	@echo "Sincronización de laboratorios"
	@echo "------------------------"
	@echo "  make sincro           - Sincroniza alumnos y aplica ApplicationSet en ArgoCD"
	@echo "  make delete           - Elimina el ApplicationSet (borra los laboratorios)"
	@echo "  make passwords        - Muestra contraseñas de Argo CD, Gitea y Checkmk"
	@echo ""
	@echo "Minikube & Utilidades"
	@echo "------------------------"
	@echo "  make start-minikube   - Inicia Minikube con Calico CNI"
	@echo "  make expose           - Expone gitea, checkmk, argocd y app-edugitops vía port-forward."
	@echo ""

# Gestión de contextos de kubectl
list-contexts:
	kubectl config get-contexts

current-context:
	@echo "Contexto actual:"
	kubectl config current-context

use-minikube:
	@echo "Cambiando contexto a Minikube..."
	kubectl config use-context $(MINIKUBE_CONTEXT)

use-eks:
	@echo "Cambiando contexto al clúster EKS..."
	kubectl config use-context $(EKS_CONTEXT)

# Despliegues del stack
argocd:
	@echo "Desplegando ArgoCD..."
	./stack/argocd.sh

gitea:
	@echo "Desplegando Gitea..."
	kubectl apply -f ./stack/gitea.yaml

gitea-init:
	@echo "Inicializando repositorio Gitea..."
	./scripts/gitea_create_and_push.sh

checkmk:
	@echo "Desplegando Checkmk..."
	kubectl apply -f ./stack/checkmk.yaml

app-edugitops:
	@echo "Desplegando app-edugitops con configuración extendida..."	
	@bash -c "set -a && source .env && set +a && envsubst '\$$APP_IMAGE \$$APP_VERSION \$$GITEA_API_URL \$$GITEA_REPO_NAME \$$GITEA_BRANCH \$$GITEA_FILE_PATH \$$GITEA_CATALOGO_PATH \$$GITEA_USER \$$GITEA_PASSWORD \$$FLASK_DEBUG \$$CHECKMK_API_USER \$$CHECKMK_API_SECRET \$$CHECKMK_SITE \$$CHECKMK_HOST_NAME \$$CHECKMK_URL \$$CHECKMK_HOST_IP' < ./stack/app-edugitops.yaml | kubectl apply -f -"

stack: argocd gitea checkmk app-edugitops
	@echo "Todos los despliegues completados."

# Sincronización de laboratorios
sincro:
	@echo "Sincronizando ArgoCD..."
	@bash -c "set -a && source .env && set +a && envsubst '\$$GITEA_REPO_URL \$$GITOPS_BASE_PATH \$$GITEA_BRANCH \$$GITEA_USER \$$GITEA_PASSWORD' < labs/applicationset.yaml | kubectl apply -f - -n argocd"

delete:
	@echo "🗑️  Eliminando ApplicationSet (destruyendo laboratorios)..."
	kubectl delete -f labs/applicationset.yaml -n argocd --ignore-not-found=true
	@echo "✅ Laboratorios eliminados de ArgoCD."

passwords:
	@echo "🔑 Credenciales del Sistema:"
	@echo ""
	@echo "--- ArgoCD ---"
	@echo "User: admin"
	@echo -n "Pass: "
	@kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "No encontrado (¿ArgoCD está desplegado?)"
	@echo ""
	@echo ""
	@echo "--- Gitea (desde .env) ---"
	@bash -c "source .env && echo \"User: \$$GITEA_USER\" && echo \"Pass: \$$GITEA_PASSWORD\""
	@echo ""
	@echo "--- Checkmk (desde .env) ---"
	@bash -c "source .env && echo \"User: \$$CHECKMK_API_USER\" && echo \"Pass: \$$CHECKMK_API_SECRET\""

# Minikube & Tools

start-minikube:
	@echo "Iniciando Minikube con Calico CNI..."
	minikube start --cni=calico

expose:
	@bash -c 'set -e; \
	  echo "Exponiendo servicios en segundo plano (logs en /tmp/port-forward-*.log)"; \
	  nohup kubectl port-forward -n gitea svc/gitea 3000:80 >/tmp/port-forward-gitea.log 2>&1 & echo $$! >/tmp/port-forward-gitea.pid; \
	  nohup kubectl port-forward -n checkmk svc/checkmk 5000:80 6557:6557 >/tmp/port-forward-checkmk.log 2>&1 & echo $$! >/tmp/port-forward-checkmk.pid; \
	  nohup kubectl port-forward -n argocd svc/argocd-server 8080:443 >/tmp/port-forward-argocd.log 2>&1 & echo $$! >/tmp/port-forward-argocd.pid; \
	  nohup kubectl port-forward -n app-edugitops svc/app-edugitops 5001:5001 >/tmp/port-forward-edugitops.log 2>&1 & echo $$! >/tmp/port-forward-edugitops.pid; \
	  echo "Servicios expuestos:"; \
	  echo "  gitea        -> http://localhost:3000/"; \
	  echo "  checkmk      -> http://localhost:5000/ (livestatus en 6557/tcp)"; \
	  echo "  argocd       -> http://localhost:8080/"; \
	  echo "  app-edugitops -> http://localhost:5001/"; \
	  echo "PIDs: gitea=$$(cat /tmp/port-forward-gitea.pid) checkmk=$$(cat /tmp/port-forward-checkmk.pid) argocd=$$(cat /tmp/port-forward-argocd.pid) edugitops=$$(cat /tmp/port-forward-edugitops.pid)"; \
	  echo "Detén con: kill $$(cat /tmp/port-forward-gitea.pid) $$(cat /tmp/port-forward-checkmk.pid) $$(cat /tmp/port-forward-argocd.pid) $$(cat /tmp/port-forward-edugitops.pid)"'