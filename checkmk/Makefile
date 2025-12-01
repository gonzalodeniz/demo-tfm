NAMESPACE ?= checkmk
MANIFEST ?= checkmk.yaml

.PHONY: help
help:
	@echo "Makefile Checkmk - opciones:"
	@echo "  make apply             -> kubectl apply -f $(MANIFEST)"
	@echo "  make delete-namespace  -> kubectl delete namespace $(NAMESPACE)"
	@echo "  make port-forward      -> kubectl port-forward -n $(NAMESPACE) svc/checkmk 5000:5000 6557:6557"

.PHONY: apply
apply:
	kubectl apply -f $(MANIFEST)

.PHONY: delete-namespace
delete-namespace:
	kubectl delete namespace $(NAMESPACE)

.PHONY: port-forward
port-forward:
	kubectl port-forward -n $(NAMESPACE) svc/checkmk 5000:5000 6557:6557
