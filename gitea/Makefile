NAMESPACE ?= gitea
MANIFEST ?= gitea.yaml

.PHONY: help
help:
	@echo "Uso: make [target]"
	@echo ""
	@echo "Targets disponibles:"
	@echo "  apply              - Aplica el manifiesto de Kubernetes"
	@echo "  port-forward       - Crea un port-forward al servicio de Gitea en el puerto 3000"
	@echo "  delete-namespace   - Elimina el namespace especificado"
	@echo "  help               - Muestra esta ayuda"
	@echo ""
	@echo "Variables:"
	@echo "  NAMESPACE          - Namespace de Kubernetes (default: gitea)"
	@echo "  MANIFEST           - Archivo de manifiesto (default: gitea.yaml)"


.PHONY: apply
apply:
	kubectl apply -f $(MANIFEST)

.PHONY: port-forward
port-forward:
	kubectl port-forward -n $(NAMESPACE) svc/gitea 3000:3000

.PHONY: delete-namespace
delete-namespace:
	kubectl delete namespace $(NAMESPACE)

.DEFAULT_GOAL := help
