# Ayuda Kubernetes
Comandos útiles de Kubernetes

## Minikube

Inicia un clúster de Minikube e instala Calico como CNI (Container Network Interface).
Calico permite definir políticas de red (NetworkPolicy) para controlar tráfico entre namespaces, pods, etc.
```
minikube start --cni=calico
```

## Servicios

Muestra información de los servicios
```
kubectl get services -n monitoring-ana-001
```

Muestra detalle de un servicio
```
kubectl describe service <nombre-del-servicio> -n monitoring-ana-001
```

Crea túnel hasta el servicio dentro del cluster de Minikube
```
minikube service grafana-service -n monitoring-ana-001 --url
```

## ArgoCD

Expone el puerto de ArgoCD para que sea accesible desde fuera del cluster
```
kubectl port-forward svc/argocd-server -n argocd 8080:443
```