.PHONY: sincro delete

sincro:
	kubectl apply -f argocd/applicationset-kustomize-monitoring.yaml -n argocd

delete:
	kubectl delete applicationset namespaces-alumnos -n argocd
