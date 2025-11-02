.PHONY: sincro delete

sincro:
	kubectl apply -f argocd/applicationset-monitoring.yaml -n argocd

delete:
	kubectl delete applicationset namespaces-alumnos -n argocd
