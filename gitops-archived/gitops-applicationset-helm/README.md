# gitops-applicationset-helm

Repositorio archivado con un flujo basado en ApplicationSet (Helm) para desplegar monitorización por alumno.

## Estructura
- `alumnos.yaml`: lista de alumnos, apps y datos utilizados por los manifiestos Helm.
- `argocd/applicationset-monitoring.yaml`: ApplicationSet de Argo CD que instancia recursos por alumno usando el chart.
- `helm-chart/`: chart Helm base para crear namespaces, Prometheus y Grafana por alumno.
- `scripts/push-alumnos.sh`: hace commit y push de cambios en `alumnos.yaml` al remoto configurado.
- `Makefile`: atajos de sincronización y limpieza.

## Makefile
- `make help`: muestra las opciones disponibles.
- `make sincro`: ejecuta `scripts/push-alumnos.sh` y aplica el ApplicationSet (`argocd/applicationset-monitoring.yaml`) en el namespace `argocd`.
- `make delete`: elimina el ApplicationSet `namespaces-alumnos` en el namespace `argocd`.
- `make expose`: port-forward en segundo plano de gitea (3000) y argocd (8080→443); PIDs y logs en `/tmp/port-forward-*.{pid,log}`.
- `make expose-service-grafana`: muestra la URL de `grafana-service` en `monitoring-ana-001` vía `minikube service --url`.
- `make expose-service-prometheus`: muestra la URL de `prometheus-service` en `monitoring-ana-001` vía `minikube service --url`.

## Requisitos
- `kubectl` apuntando al clúster correcto y permisos en `argocd`.
- `git` configurado con el remoto adecuado para `push-alumnos.sh`.
- `argocd` instalado en el clúster (el ApplicationSet se aplica en `argocd`).

## Notas
- Este flujo está archivado; los nombres de ApplicationSet y chart asumen la estructura incluida. Ajusta los manifiestos si cambian rutas o nombres.
