# GitOps y ArgoCD
Explica los pasos para desplegar contenedores en kubernetes a partir de git utilizando ArgoCD.

## Estructura de directorios

```
.
├── README.md
├── alumnos.txt
├── argocd
│   ├── alumnos-deployment-application.yaml
│   └── alumnos-namespace-application.yaml
├── crea-alumnos-deploy.sh
├── crea-alumnos-namespace.sh
├── deployments
│   ├── alumno-ana-0001.yaml
│   └── alumno-juan-0002.yaml
├── namespaces
│   ├── alumno-ana-0001.yaml
│   └── alumno-juan-0002.yaml
└── templates
    ├── namespace-template.yaml
    └── nginx-deploy-template.yaml

```
donde:
* alumnos.txt: Fichero csv con el nombre del alumno y su id
* argocd: Manifiesto para crear las aplicaciones en ArgoCD y despliegue en Kubernetes
* crea-alumnos-deploy.sh: Crea los manifiestos deployment de los alumnos a partir de plantillas
* crea-alumnos-namesplaces.sh: Crea los manifiestos namespaces de los alumnos a partir de plantillas
* templates: plantillas para crear los manifiestos de kubernetes



## Preparación del entorno
Arrancar minikube y exponer el servicio de ArgoCD
```
minikube start
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Mostrar contraseña del usuario *admin* de ArgoCD
```
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode && echo
```

## Despliegues con ArgoCD
Subir una nueva aplicación

```
kubectl apply -f argocd/alumnos-namespace-application.yaml 
kubectl apply -f argocd/alumnos-deployment-application.yaml 
```

Construir manifiestos de los alumnos a partir de las plantillas

```
./crea-alumnos-namespace.sh
./crea-alumnos-deploy.sh
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
kubectl get all -n alumno-ana-0001
```

Ver el detalle de un servicio
```
kubectl get svc nginx-ana-0001-svc -n alumno-ana-0001 -o wide

NAME                 TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
nginx-ana-0001-svc   NodePort   10.101.135.83   <none>        80:30001/TCP   14m app=nginx-ana-0001
```

Ver la URL de un servicio y hacer túnel para acceder desde fuera del cluster al servicio
```
minikube service nginx-ana-0001-svc -n alumno-ana-0001 --url
minikube tunnel
```


