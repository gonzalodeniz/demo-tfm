# Nombre del contexto EKS (ajústalo si es distinto en tu kubeconfig)
EKS_CONTEXT = arn:aws:eks:us-east-1:202974436470:cluster/cluster-tfm
MINIKUBE_CONTEXT = minikube

.PHONY: help use-minikube use-eks list-contexts current-context argocd gitea checkmk apps

help:
	@echo ""
	@echo "Opciones disponibles:"
	@echo "  make help             - Muestra esta ayuda"
	@echo "  make list-contexts    - Lista todos los contextos disponibles en kubectl"
	@echo "  make current-context  - Muestra el contexto actual de kubectl"
	@echo "  make use-minikube     - Cambia el contexto de kubectl a Minikube"
	@echo "  make use-eks          - Cambia el contexto de kubectl al clúster EKS"
	@echo "  make argocd           - Despliega ArgoCD en EKS"
	@echo "  make gitea            - Despliega Gitea en EKS"
	@echo "  make checkmk          - Despliega Checkmk en EKS"
	@echo "  make apps             - Despliega ArgoCD, Gitea y Checkmk en EKS"
	@echo ""

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

argocd:
	@echo "Desplegando ArgoCD en EKS..."
	./provision/argocd-eks.sh

gitea:
	@echo "Desplegando Gitea en EKS..."
	kubectl apply -f ./provision/gitea-eks.yaml

checkmk:
	@echo "Desplegando Checkmk en EKS..."
	kubectl apply -f ./provision/checkmk-eks.yaml

apps: argocd gitea checkmk
	@echo "Todos los despliegues completados."
