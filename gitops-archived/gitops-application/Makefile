.PHONY: help run sincro delete expose expose-service-grafana expose-service-prometheus

help:
	@echo "Opciones disponibles:"
	@echo "  make run     - Crea monitorización, hace push de alumnos y lanza sincro."
	@echo "  make sincro  - Aplica la application-monitoring en el namespace argocd."
	@echo "  make delete  - Borra monitorización y sincroniza eliminación."
	@echo "  make expose  - Port-forward de gitea (3000) y argocd (8080) en segundo plano."
	@echo "  make expose-service-grafana    - Abre grafana-service en minikube (monitoring-ana-001)."
	@echo "  make expose-service-prometheus - Abre prometheus-service en minikube (monitoring-ana-001)."

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
	argocd app sync alumnos-monitoring --prune
	sleep 5
	kubectl delete application alumnos-monitoring -n argocd

expose:
	@bash -c 'set -e; \
	  echo "Exponiendo servicios en segundo plano (logs en /tmp/port-forward-*.log)"; \
	  nohup kubectl port-forward -n gitea svc/gitea 3000:3000 >/tmp/port-forward-gitea.log 2>&1 & echo $$! >/tmp/port-forward-gitea.pid; \
	  nohup kubectl port-forward -n argocd svc/argocd-server 8080:443 >/tmp/port-forward-argocd.log 2>&1 & echo $$! >/tmp/port-forward-argocd.pid; \
	  echo "PIDs: gitea=$$(cat /tmp/port-forward-gitea.pid) argocd=$$(cat /tmp/port-forward-argocd.pid)"; \
	  echo "Detén con: kill $$(cat /tmp/port-forward-gitea.pid) $$(cat /tmp/port-forward-argocd.pid)"; \
	'

expose-service-grafana:
	minikube service grafana-service -n monitoring-ana-001 --url

expose-service-prometheus:
	minikube service prometheus-service -n monitoring-ana-001 --url