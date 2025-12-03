# GitOps y ArgoCD
Explica los pasos para desplegar contenedores en kubernetes a partir de git utilizando ArgoCD.

## Estructura de directorios

```
.
├── Makefile
├── README.md
├── alumnos
│   ├── grafana
│   ├── namespaces
│   ├── networkpolicies
│   └── prometheus
├── alumnos.txt
├── argocd
│   └── application-monitoring.yaml
├── scripts
│   ├── crea-monitoring.sh
│   └── delete-monitoring.sh
└── templates
    ├── grafana
    ├── namespace-template.yaml
    ├── networkpolicies-template.yaml
    └── prometheus

```
donde:
- `alumnos.txt`: fichero CSV con el nombre del alumno y su id.
- `argocd`: manifiesto Application de ArgoCD que sincroniza todos los recursos generados.
- `scripts/crea-monitoring.sh`: genera todos los manifiestos a partir de las plantillas.
- `scripts/delete-monitoring.sh`: elimina los manifiestos generados.
- `templates`: plantillas parametrizadas de Kubernetes (Grafana, Prometheus, NetworkPolicies y Namespace).

## Makefile (atajos)
- `make help`: muestra las opciones disponibles.
- `make run`: crea monitorización, hace push de alumnos y lanza `sincro`.
- `make sincro`: aplica `argocd/application-monitoring.yaml` en el namespace `argocd`.
- `make delete`: borra monitorización y sincroniza la eliminación, luego elimina la Application.
- `make expose`: port-forward en segundo plano de gitea (3000) y argocd (8080→443); PIDs y logs en `/tmp/port-forward-*.{pid,log}`.
- `make expose-service-grafana`: abre `grafana-service` en `monitoring-ana-001` vía `minikube service`.
- `make expose-service-prometheus`: abre `prometheus-service` en `monitoring-ana-001` vía `minikube service`.

## Formato de namespaces

Independientemente de si se despliega con una Application, un ApplicationSet-Helm o un ApplicationSet-Kustomize,
el namespace de cada alumno sigue el mismo patrón:

```
monitoring-<nombre-normalizado>-<id-normalizado>
```

Los scripts normalizan el nombre (minúsculas y `-` en lugar de espacios) y conservan el identificador (por ejemplo `001`),
de modo que casos como `Ana,001` generan siempre el namespace `monitoring-ana-001`.



## Preparación del entorno

### Arrancar minikube con soporte a NetworkPolicy
```
minikube start --cni=calico
```

### Instalar ArgoCD (si no existe)
Instala ArgoCD en el cluster ejecutando:
```
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### Arrancar minikube y exponer el servicio de ArgoCD
```
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### Mostrar contraseña del usuario *admin* de ArgoCD
```
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode && echo
```

### Login en ArgoCD desde la CLI
Instala la CLI de ArgoCD si no la tienes:
```
brew install argocd   # macOS
sudo apt install argocd   # Ubuntu (si está disponible)
```
Haz login usando la contraseña obtenida:
```
argocd login localhost:8080 --username admin --password <contraseña>
```

### Modificar la contraseña del usuario admin
Cambia la contraseña desde la CLI:
```
argocd account update-password --account admin --current-password xxx --new-password yyy
```


## Despliegues con ArgoCD
Desplegar la aplicación que orquesta todo el stack:

```
kubectl apply -f argocd/application-monitoring.yaml
```

Construir o actualizar los manifiestos a partir de las plantillas:

```
bash scripts/crea-monitoring.sh
```

Borrar los manifiestos generados si es necesario:

```
bash scripts/delete-monitoring.sh
```

## Comandos de verificación
Ver los namespace en minikube
```
kubectl get namespaces
```

Borrar namespaces
```
kubectl delete namespace nombre-namespaces
```

Ver todos los objetos de un namespace
```
kubectl get all -n monitoring-ana-001
```

Ver el detalle de un servicio
```
kubectl get svc grafana-service -n monitoring-ana-001 -o wide

NAME              TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
grafana-service   NodePort   10.101.135.83   <none>        3000:30000/TCP   14m app=grafana
```

Ver la URL de un servicio y hacer túnel para acceder desde fuera del cluster al servicio
```
minikube service grafana-service -n monitoring-ana-001 --url
minikube tunnel
```
