.PHONY: help sincro delete expose

help:
	@echo "Opciones disponibles:"
	@echo "  make sincro   - Sincroniza alumnos, aplica ApplicationSet y crea reglas de monitorización."
	@echo "  make delete   - Elimina el ApplicationSet students-appset en el namespace argocd y borra las reglas de monitorización."
	@echo "  make expose   - Expone gitea, checkmk, argocd y app-edugitops vía port-forward."

sincro:
	bash scripts/push-alumnos.sh
	kubectl apply -f applicationset.yaml -n argocd
	python3 scripts/monitoriza-laboratorios.py

delete:
	kubectl delete applicationset student-labs-appset -n argocd
	bash scripts/checkmk-borrar-reglas-http2.sh

expose:
	@bash -c 'set -e; \
	  echo "Exponiendo servicios en segundo plano (logs en /tmp/port-forward-*.log)"; \
	  nohup kubectl port-forward -n gitea svc/gitea 3000:3000 >/tmp/port-forward-gitea.log 2>&1 & echo $$! >/tmp/port-forward-gitea.pid; \
	  nohup kubectl port-forward -n checkmk svc/checkmk 5000:5000 6557:6557 >/tmp/port-forward-checkmk.log 2>&1 & echo $$! >/tmp/port-forward-checkmk.pid; \
	  nohup kubectl port-forward -n argocd svc/argocd-server 8080:443 >/tmp/port-forward-argocd.log 2>&1 & echo $$! >/tmp/port-forward-argocd.pid; \
	  nohup kubectl port-forward -n app-edugitops svc/app-edugitops 5001:5001 >/tmp/port-forward-edugitops.log 2>&1 & echo $$! >/tmp/port-forward-edugitops.pid; \
	  echo "Servicios expuestos:"; \
	  echo "  gitea        -> http://localhost:3000/"; \
	  echo "  checkmk      -> http://localhost:5000/ (livestatus en 6557/tcp)"; \
	  echo "  argocd       -> http://localhost:8080/"; \
	  echo "  app-edugitops -> http://localhost:5001/"; \
	  echo "PIDs: gitea=$$(cat /tmp/port-forward-gitea.pid) checkmk=$$(cat /tmp/port-forward-checkmk.pid) argocd=$$(cat /tmp/port-forward-argocd.pid) edugitops=$$(cat /tmp/port-forward-edugitops.pid)"; \
	  echo "Detén con: kill $$(cat /tmp/port-forward-gitea.pid) $$(cat /tmp/port-forward-checkmk.pid) $$(cat /tmp/port-forward-argocd.pid) $$(cat /tmp/port-forward-edugitops.pid)"'