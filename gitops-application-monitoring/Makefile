.PHONY: run sincro delete_all

run:
	bash scripts/crea-monitoring.sh

sincro:
	kubectl apply -f argocd/application-monitoring.yaml -n argocd

delete_all:
	bash scripts/delete-monitoring.sh