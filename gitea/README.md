# Gitea en Minikube

Gitea es una plataforma ligera de forja de repositorios Git (similar a GitHub/GitLab) escrita en Go y de código abierto.

## Prerrequisitos
- Minikube instalado y corriendo (`minikube start`).
- `kubectl` apuntando al contexto de Minikube.

## Despliegue
1) Aplicar los manifiestos:
```
kubectl apply -f gitea.yaml
```
2) Comprobar recursos:
```
kubectl get pods,svc,pvc -n gitea
```

## Credenciales por defecto
- Usuario admin: `admin`
- Contraseña: `admin123`
Se crean automáticamente en el `initContainer` del Deployment; si el usuario ya existe se fuerza la contraseña indicada. Puedes cambiarlos editando `gitea.yaml` en la sección `Secret gitea-admin` o `init-gitea-admin`.

## Acceso web (port-forward)
Forward del servicio al puerto local 3000:
```
kubectl port-forward -n gitea svc/gitea 3000:3000
```
Luego abre `http://localhost:3000` en el navegador.

## Acceso alternativo (NodePort con minikube service)
Si prefieres usar NodePort (ya definido en `gitea.yaml`):
```
minikube service gitea -n gitea --url
```
Abre la URL devuelta (usa el puerto 30080 del nodo).

## Verificar funcionamiento
- Pod en `Running`: `kubectl get pods -n gitea`
- Salud HTTP: `curl -I http://localhost:3000` (tras port-forward) debería devolver 200/302.

## Logs y diagnóstico
```
kubectl logs -n gitea deploy/gitea
kubectl describe pod -n gitea -l app=gitea
```
Si el PVC falla, revisa `kubectl get pvc -n gitea` y describe el PVC.

## Primeros pasos en Gitea
1) Inicia sesión con `admin` / `admin123`.
2) Ajusta opciones básicas en Settings (nombre de instancia, correo SMTP si aplica).
3) Crea una organización o un repositorio nuevo desde la UI.
4) Para subir un repositorio existente:
```
git remote add origin http://localhost:3000/<tu-usuario>/<repo>.git
git push -u origin main
```
5) Habilita claves SSH si quieres usar el puerto 30022 (NodePort) para pushes por SSH.
