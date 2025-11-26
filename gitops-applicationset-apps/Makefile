.PHONY: sincro delete

sincro:
	bash scripts/push-alumnos.sh
	kubectl apply -f applicationset.yaml -n argocd

delete:
	kubectl delete applicationset students-appset -n argocd
