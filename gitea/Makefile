NAMESPACE ?= gitea
MANIFEST ?= gitea.yaml

.PHONY: apply
apply:
	kubectl apply -f $(MANIFEST)

.PHONY: port-forward
port-forward:
	kubectl port-forward -n $(NAMESPACE) svc/gitea 3000:3000

.PHONY: delete-namespace
delete-namespace:
	kubectl delete namespace $(NAMESPACE)
