# Variables de contexto (ajústalas según tu entorno)
EKS_CONTEXT = arn:aws:eks:us-east-1:202974436470:cluster/cluster-tfm
MINIKUBE_CONTEXT = minikube

.PHONY: help list-contexts current-context use-minikube use-eks argocd gitea gitea-init checkmk app-edugitops stack sincro delete-labs delete-stack passwords start-minikube expose

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
	@echo "  make delete-labs      - Elimina el ApplicationSet y los laboratorios"	
	@echo "  make delete-stack     - Borra todo el stack (Apps + Laboratorios)"
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
	./stack/argocd.sh

gitea:
	kubectl apply -f ./stack/gitea.yaml

gitea-init:
	./scripts/gitea_create_and_push.sh

checkmk:
	kubectl apply -f ./stack/checkmk.yaml

app-edugitops:
	./scripts/deploy_app.sh

stack: argocd gitea checkmk app-edugitops
	@echo "Todos los despliegues completados."

# Sincronización de laboratorios
sincro:
	./scripts/sync_labs.sh

delete-labs:
	./scripts/delete_labs.sh

delete-stack:
	./scripts/delete_stack.sh

passwords:
	./scripts/show_passwords.sh

# Minikube & Utilidades
start-minikube:
	@echo "Iniciando Minikube con Calico CNI..."
	minikube start --cni=calico

expose:
	./scripts/expose_services.sh