.PHONY: run sincro delete

run:
	bash scripts/crea-monitoring.sh
	sleep 1
	bash scripts/push-alumnos.sh
	$(MAKE) sincro

sincro:
	kubectl apply -f argocd/application-monitoring.yaml -n argocd

delete:
	bash scripts/delete-monitoring.sh
	sleep 2
	bash scripts/push-alumnos.sh
	argocd app sync alumnos-monitoring
	sleep 5
	kubectl delete application alumnos-monitoring -n argocd
	
