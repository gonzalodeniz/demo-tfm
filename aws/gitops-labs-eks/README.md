# gitops-labs

Directorio de laboratorio GitOps para desplegar y monitorizar aplicaciones de alumnos en Kubernetes mediante Argo CD y Checkmk. El ApplicationSet consume el repo `http://a918d57187f9347289c750a4d75c510e-320216334.us-east-1.elb.amazonaws.com/admin/demo-tfm.git` y el contenido bajo `aws/gitops-labs-eks/`.

## Estructura
- `alumnos.yaml`: fuente de verdad con la lista de alumnos, apps y URLs de chequeo HTTP.
- `applicationset.yaml`: ApplicationSet de Argo CD que instancia los despliegues por alumno (usa `aws/gitops-labs-eks/base` como plantilla Helm en el repo anterior). Se rellena vía `envsubst` usando las variables de `.env`.
- `base/`: chart Helm con manifiestos de Prometheus, Grafana, namespace, ConfigMaps y NetworkPolicy (sin PVCs; usa almacenamiento efímero `emptyDir`).
- `.env`: variables de endpoints (Gitea, Checkmk, Argo CD) y rutas usadas por `make`/scripts. Incluye `GITEA_REPO_URL`, `GITOPS_BASE_PATH`, `CHECKMK_URL`, `ARGOCD_URL`, `CHECKMK_HOST_NAME`, `CHECKMK_HOST_IP`, etc. Los scripts `.sh` y `monitoriza-laboratorios.py` la cargan automáticamente si existe en el directorio.
- `scripts/`:
  - `push-alumnos.sh`: commitea y hace push de cambios en `alumnos.yaml` al remote `gitea`.
  - `monitoriza-laboratorios.py`: borra reglas HTTPv2 existentes en Checkmk y crea nuevas a partir de `alumnos.yaml` (reemplaza al `.sh`; invocar con `python3`).
  - `checkmk-borrar-reglas-http2.sh`: elimina todas las reglas `active_checks:httpv2` y activa cambios.
  - `checkmk-crear-regla-http2.sh`: crea una regla HTTPv2 y activa cambios.
  - `checkmk-crear-host.sh`: crea un host en Checkmk usando `CHECKMK_HOST_NAME`/`CHECKMK_HOST_IP` de `.env` (no requiere parámetros).
  - `checkmk-borrar-host.sh`: elimina el host indicado en `CHECKMK_HOST_NAME` usando las credenciales/endpoint de `.env`.
- `Makefile`: atajos para sincronizar o eliminar el ApplicationSet.

### Sobre `alumnos.yaml`
Es la fuente de datos que describe cada laboratorio/alumno. Estructura por elemento de la lista:
- `nombre`: identificador legible (ej: `alumno-juan`).
- `id`: identificador corto (ej: `"001"`).
- `apps`: lista de apps a desplegar por alumno (ej: `prometheus`, `grafana`).
- `check-http`: lista de URLs HTTP que Checkmk vigilará; el orden debe corresponder 1:1 con `apps`.

Ejemplo:
```yaml
- nombre: alumno-juan
  id: "001"
  apps:
    - prometheus
    - grafana
  check-http:
    - http://prometheus-service.alumno-juan.svc.cluster.local:9090
    - http://grafana-service.alumno-juan.svc.cluster.local:3000
```
Si `apps` y `check-http` no tienen la misma longitud, el proceso se detiene con error para evitar configuraciones inconsistentes.

## Requisitos previos
- `kubectl` apuntando al clúster correcto y permisos para aplicar/eliminar recursos en `argocd`.
- Argo CD desplegado y accesible.
- Checkmk accesible en `http://127.0.0.1:5000/cmk` con usuario `cmkadmin/admin123` (ajusta en scripts si difiere).
- `git` configurado con remote `gitea` apuntando a `http://a918d57187f9347289c750a4d75c510e-320216334.us-east-1.elb.amazonaws.com/admin/demo-tfm.git` (o ajusta `GITEA_REMOTE_NAME` en `.env`).
- `python3` con PyYAML (`python3 -m pip install pyyaml`), `curl` y `jq`.
- `curl` y `jq` disponibles para las llamadas API.
- `.env` cargado en el directorio (`make` lo exporta automáticamente); revisa y ajusta `GITEA_REPO_URL`, `GITOPS_BASE_PATH`, `CHECKMK_URL`, `CHECKMK_SITE`, `CHECKMK_API_USER`, `CHECKMK_API_SECRET`, `ARGOCD_URL`.

## Despliegue en AWS EKS (sin PVC)
No se crean PVC ni storage class; Prometheus y Grafana usan `emptyDir`, así que los datos se pierden si el pod se recrea. Los servicios se exponen como `LoadBalancer` en AWS.

1. Prepara el contexto de kubeconfig apuntando al clúster EKS y verifica acceso: `aws eks update-kubeconfig --name <cluster>` y `kubectl get ns`.
2. Asegura que Argo CD esté instalado en EKS y tenga acceso al repo `GITEA_REPO_URL` y a la ruta `GITOPS_BASE_PATH` (por defecto `aws/gitops-labs-eks/`). Ajusta `.env` si cambian.
3. Edita `alumnos.yaml` con los alumnos/apps que necesites y revisa `.env`.
4. Aplica el ApplicationSet en EKS: `make sincro` (usa `envsubst` sobre `applicationset.yaml` y luego recrea reglas en Checkmk) o manualmente `envsubst < applicationset.yaml | kubectl apply -f - -n argocd`.
5. Espera a que Argo CD cree las apps y obtén las IP/DNS públicos de los servicios:
   - `kubectl get svc -n <nombre>` y revisa `EXTERNAL-IP` de `grafana-service` y `prometheus-service`.
6. Cuando quieras limpiar, elimina el ApplicationSet: `kubectl delete applicationset student-labs-appset -n argocd` (o `make delete` si quieres además limpiar Checkmk).

## Uso del Makefile
- `make help`: muestra las opciones disponibles.
- `make sincro`: 
  1) ejecuta `scripts/push-alumnos.sh` para subir cambios en `alumnos.yaml`; 
  2) aplica `applicationset.yaml` en el namespace `argocd` usando `envsubst` y las variables de `.env`; 
  3) recrea reglas HTTPv2 en Checkmk en base a `alumnos.yaml`.
- `make delete`: elimina el ApplicationSet `students-appset` en el namespace `argocd`.
- `make expose`: lanza `kubectl port-forward` en segundo plano para gitea (3000), checkmk (5000, 6557) y argocd (8080). Registra PIDs en `/tmp/port-forward-*.pid` y logs en `/tmp/port-forward-*.log`; deténlos con `kill $(cat /tmp/port-forward-*.pid)` o matando los PIDs listados.
- `make urls`: muestra las URLs de Gitea, Checkmk y Argo CD cargadas desde `.env`.
- `make passwords`: muestra las credenciales admin de Argo CD (secret `argocd-initial-admin-secret`), Gitea (secret `gitea-admin`) y Checkmk (valores de `.env`).

## Flujos principales
### Alta o cambio de alumno/app
1. Edita `alumnos.yaml` añadiendo/ajustando `nombre`, `apps` y `check-http` (mismo orden y longitud).
2. Ejecuta `make sincro` para:
   - subir el cambio a Git,
   - actualizar el ApplicationSet en Argo CD,
   - recrear reglas HTTPv2 en Checkmk vía `monitoriza-laboratorios.py`.
3. Verifica en Argo CD el despliegue y en Checkmk las nuevas reglas.

### Limpieza de despliegues
1. Ejecuta `make delete` para eliminar el ApplicationSet y sus aplicaciones asociadas.
2. Si quieres limpiar reglas HTTPv2 manualmente, puedes lanzar `scripts/checkmk-borrar-reglas-http2.sh`.

## Notas y configuración
- Los scripts asumen `TARGET_HOST_NAME=minikube` y URLs de `check-http` ya resolubles desde Checkmk.
- Si cambian credenciales o endpoint de Checkmk, edita `scripts/checkmk-*.sh`.
- `monitoriza-laboratorios.py` espera `alumnos.yaml` en este directorio (`aws/gitops-labs-eks/`). Ajusta la ruta si se mueve.

## Resolución de problemas
- **Error PyYAML no encontrado**: instala con `python3 -m pip install pyyaml`.
- **curl/jq no encontrado**: instala los binarios en la máquina donde se ejecutan los scripts.
- **Apps y check-http desalineados**: cada entrada debe tener el mismo número de elementos en `apps` y `check-http`.
- **Checkmk no aplica cambios**: revisa conectividad al endpoint y credenciales, o reintenta activación con `checkmk-borrar-reglas-http2.sh` / `checkmk-crear-regla-http2.sh`.
