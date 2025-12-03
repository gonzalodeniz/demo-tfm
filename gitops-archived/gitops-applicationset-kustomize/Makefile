.PHONY: help sincro delete expose expose-service-grafana expose-service-prometheus

help:
	@echo "Opciones disponibles:"
	@echo "  make sincro  - Push de alumnos.yaml y aplica el ApplicationSet de monitoring."
	@echo "  make delete  - Elimina el ApplicationSet namespaces-alumnos en argocd."
	@echo "  make expose  - Port-forward de gitea (3000) y argocd (8080) en segundo plano."
	@echo "  make expose-service-grafana    - URL de grafana-service (monitoring-ana-001) via minikube."
	@echo "  make expose-service-prometheus - URL de prometheus-service (monitoring-ana-001) via minikube."

sincro:
	bash scripts/push-alumnos.sh
	kubectl apply -f argocd/applicationset-kustomize.yaml -n argocd

delete:
	kubectl delete applicationset namespaces-alumnos -n argocd

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
