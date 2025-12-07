-include .env
ifneq (,$(wildcard .env))
export $(shell sed -n 's/^\([A-Za-z_][A-Za-z0-9_]*\)=.*/\1/p' .env)
endif

.PHONY: help sincro delete expose urls passwords

help:
	@echo "Opciones disponibles:"
	@echo "  make sincro   - Sincroniza alumnos, aplica ApplicationSet y crea reglas de monitorización."
	@echo "  make delete   - Elimina el ApplicationSet students-appset en el namespace argocd y borra las reglas de monitorización."	
	@echo "  make urls     - Muestra las URLs configuradas en .env (Gitea, Checkmk, Argo CD)."
	@echo "  make passwords- Muestra contraseñas de Argo CD, Gitea y Checkmk."

sincro:
	bash scripts/push-alumnos.sh
	# Cargamos .env (set -a exporta las variables automáticamente) antes de envsubst
	@bash -c 'set -a && . ./.env && set +a && envsubst < applicationset.yaml | kubectl apply -f - -n argocd'
	python3 scripts/monitoriza-laboratorios.py

delete:
	kubectl delete applicationset student-labs-appset -n argocd
	bash scripts/checkmk-borrar-reglas-http2.sh



urls:
	@echo "GITEA_URL=${GITEA_URL}"
	@echo "GITEA_REPO_URL=${GITEA_REPO_URL}"
	@echo "CHECKMK_URL=${CHECKMK_URL}"
	@echo "ARGOCD_URL=${ARGOCD_URL}"

passwords:
	@bash -c 'set -euo pipefail; \
	  if [[ -f .env ]]; then set -a; . ./.env; set +a; fi; \
	  echo "--------------------------------------------------"; \
	  echo "Argo CD"; \
	  echo "  User: admin"; \
	  if kubectl get secret argocd-initial-admin-secret -n argocd >/dev/null 2>&1; then \
	    echo -n "  Password: "; kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d; echo ""; \
	  else \
	    echo "  Password: [No se encontró el secret]"; \
	  fi; \
	  echo ""; \
	  echo "Gitea"; \
	  echo "  User: gitea_admin"; \
	  if kubectl get secret gitea-admin -n gitea >/dev/null 2>&1; then \
	    echo -n "  Password: "; kubectl get secret gitea-admin -n gitea -o jsonpath="{.data.password}" | base64 -d; echo ""; \
	  else \
	    echo "  Password: [No se encontró el secret]"; \
	  fi; \
	  echo ""; \
	  echo "Checkmk"; \
	  echo "  User: $${CHECKMK_API_USER:-cmkadmin}"; \
	  echo "  Password: $${CHECKMK_API_SECRET:-admin123}"; \
	  echo "--------------------------------------------------"; \
	'