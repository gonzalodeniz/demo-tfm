.PHONY: help install password login expose

help:
	@echo "Opciones disponibles:"
	@echo "  make install   - Crea namespace argocd e instala los manifiestos oficiales."
	@echo "  make password  - Muestra la contraseña inicial (argocd-initial-admin-secret)."
	@echo "  make login     - Hace login CLI contra localhost:8080 con admin/1q2w3e4R. (--insecure)."
	@echo "  make expose    - Port-forward del servidor Argo CD en segundo plano (8080->443)."

install:
	kubectl create namespace argocd
	kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

password:
	kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo

login:
	argocd login localhost:8080 --username admin --password 1q2w3e4R. --insecure

expose:
	@bash -c 'set -e; \
	  echo "Exponiendo argocd-server en segundo plano (log: /tmp/argocd-port-forward.log, PID en /tmp/argocd-port-forward.pid)"; \
	  nohup kubectl port-forward svc/argocd-server -n argocd 8080:443 >/tmp/argocd-port-forward.log 2>&1 & echo $$! >/tmp/argocd-port-forward.pid; \
	  echo "PID: $$(cat /tmp/argocd-port-forward.pid)"; \
	  echo "Detén con: kill $$(cat /tmp/argocd-port-forward.pid)"; \
	'
