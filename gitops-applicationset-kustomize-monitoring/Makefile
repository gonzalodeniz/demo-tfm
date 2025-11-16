.PHONY: sincro delete

sincro:
	bash scripts/push-alumnos.sh
	kubectl apply -f argocd/applicationset-kustomize-monitoring.yaml -n argocd

delete:
	kubectl delete applicationset namespaces-alumnos -n argocd
