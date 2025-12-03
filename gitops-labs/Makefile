.PHONY: help sincro delete

help:
	@echo "Opciones disponibles:"
	@echo "  make sincro   - Sincroniza alumnos, aplica ApplicationSet y crea reglas de monitorización."
	@echo "  make delete   - Elimina el ApplicationSet students-appset en el namespace argocd y borra las reglas de monitorización."

sincro:
	bash scripts/push-alumnos.sh
	kubectl apply -f applicationset.yaml -n argocd
	python3 scripts/monitoriza-laboratorios.py

delete:
	kubectl delete applicationset student-labs-appset -n argocd
	bash scripts/checkmk-borrar-reglas-http2.sh
