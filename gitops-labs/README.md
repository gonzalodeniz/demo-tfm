# gitops-labs

Directorio de laboratorio GitOps para desplegar y monitorizar aplicaciones de alumnos en Kubernetes mediante Argo CD y Checkmk.

## Estructura
- `alumnos.yaml`: fuente de verdad con la lista de alumnos, apps y URLs de chequeo HTTP.
- `applicationset.yaml`: ApplicationSet de Argo CD que instancia los despliegues por alumno (usa `base/` como plantilla Helm).
- `base/`: chart Helm con manifiestos de Prometheus, Grafana, namespace, PVCs, ConfigMaps y NetworkPolicy.
- `scripts/`:
  - `push-alumnos.sh`: commitea y hace push de cambios en `alumnos.yaml` al remote `gitea`.
  - `monitoriza-laboratorios.py`: borra reglas HTTPv2 existentes en Checkmk y crea nuevas a partir de `alumnos.yaml` (reemplaza al `.sh`; invocar con `python3`).
  - `checkmk-borrar-reglas-http2.sh`: elimina todas las reglas `active_checks:httpv2` y activa cambios.
  - `checkmk-crear-regla-http2.sh`: crea una regla HTTPv2 y activa cambios.
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
- `git` configurado con remote `gitea`.
- `python3` con PyYAML (`python3 -m pip install pyyaml`), `curl` y `jq`.
- `curl` y `jq` disponibles para las llamadas API.

## Uso del Makefile
- `make help`: muestra las opciones disponibles.
- `make sincro`: 
  1) ejecuta `scripts/push-alumnos.sh` para subir cambios en `alumnos.yaml`; 
  2) aplica `applicationset.yaml` en el namespace `argocd`; 
  3) recrea reglas HTTPv2 en Checkmk en base a `alumnos.yaml`.
- `make delete`: elimina el ApplicationSet `students-appset` en el namespace `argocd`.

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
- `monitoriza-laboratorios.py` espera `alumnos.yaml` en el directorio raíz del proyecto (`gitops-labs`). Ajusta la ruta si se mueve.

## Resolución de problemas
- **Error PyYAML no encontrado**: instala con `python3 -m pip install pyyaml`.
- **curl/jq no encontrado**: instala los binarios en la máquina donde se ejecutan los scripts.
- **Apps y check-http desalineados**: cada entrada debe tener el mismo número de elementos en `apps` y `check-http`.
- **Checkmk no aplica cambios**: revisa conectividad al endpoint y credenciales, o reintenta activación con `checkmk-borrar-reglas-http2.sh` / `checkmk-crear-regla-http2.sh`.
