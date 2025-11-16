.PHONY: run sincro delete

run:
	bash scripts/crea-monitoring.sh

sincro:
	kubectl apply -f argocd/application-monitoring.yaml -n argocd

delete:
	bash scripts/delete-monitoring.sh
	kubectl delete application alumnos-monitoring -n argocd
	bash scripts/push-alumnos.sh
