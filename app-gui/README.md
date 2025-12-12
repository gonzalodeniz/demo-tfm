¡Excelente\! Me alegra saber que funcionó.

Aquí tienes el archivo `README.md` completo, explicando los pasos para que tu aplicación Flask se ejecute dentro de Minikube y pueda usar `kubectl` gracias a la configuración de RBAC.

## 🚀 Despliegue de Flask (Kubectl Client) en Minikube

Este proyecto demuestra cómo ejecutar una aplicación Python/Flask que necesita interactuar con la API de Kubernetes (usando `kubectl`) directamente desde dentro del cluster, utilizando la configuración de **Service Accounts (RBAC)** en lugar de montar archivos de configuración locales.

### Prerrequisitos

  * **Minikube:** Debe estar instalado y en ejecución (`minikube start`).
  * **Docker:** Debe estar instalado.
  * **Archivos necesarios:**
      * `Dockerfile`
      * `app.py`
      * `minikube-deployment.yaml`

-----

### Pasos de Ejecución

Sigue estos pasos en orden para construir la imagen y desplegar la aplicación en Minikube.

#### 1\. Conectar Docker al Entorno de Minikube

Antes de construir la imagen, es **fundamental** indicarle a tu terminal que use el demonio de Docker interno de Minikube. Esto asegura que la imagen se guarde directamente en el clúster local, y no en tu Docker local.

Ejecuta el siguiente comando en tu terminal:

```bash
eval $(minikube docker-env)
```

> **Verificación:** Si ejecutas `docker images` ahora, solo deberías ver las imágenes internas que usa Minikube.

#### 2\. Construir la Imagen de Docker

Desde el directorio donde se encuentran tu `Dockerfile` y `app.py`, construye la imagen usando el nombre referenciado en el manifiesto (`minikube-deployment.yaml`):

```bash
docker build -t flask-k8s-client:local .
```

> **Importante:** El tag `:local` es clave, y el `imagePullPolicy: Never` en el manifiesto asegura que Minikube busque esta imagen que acabas de construir localmente.

#### 3\. Desplegar los Recursos en Minikube (RBAC y App)

Aplica el manifiesto que crea el `ServiceAccount`, los permisos (RBAC) y el `Deployment` de la aplicación.

```bash
kubectl apply -f minikube-deployment.yaml
```

Verás una salida similar a esta (sin el error de puerto):

```
serviceaccount/flask-minikube-sa created
clusterrole.rbac.authorization.k8s.io/service-viewer-role created
clusterrolebinding.rbac.authorization.k8s.io/service-viewer-binding created
deployment.apps/flask-k8s-app created
service/flask-k8s-service created
```

#### 4\. Verificar el Estado del Despliegue

Asegúrate de que el Pod se ha iniciado correctamente:

```bash
kubectl get pods
```

Si el estado es `Running`, puedes pasar al siguiente paso.

#### 5\. Acceder a la Aplicación

Minikube simplifica la forma de acceder a los servicios de tipo `NodePort`. Ejecuta este comando para abrir automáticamente tu navegador en la dirección correcta:

```bash
minikube service flask-k8s-service --url
```

Esto abrirá la URL de tu aplicación, donde podrás navegar a la ruta `/services` y ver la salida de `kubectl get services` desde el Pod.

-----

### Limpieza (Opcional)

Para eliminar todos los recursos desplegados y liberar espacio en Minikube:

1.  Elimina el despliegue:
    ```bash
    kubectl delete -f minikube-deployment.yaml
    ```
2.  Desconecta el Docker de Minikube y regresa al Docker de tu sistema host:
    ```bash
    eval $(minikube docker-env -u)
    ```

Espero que este README sea claro y útil para el uso continuado del proyecto. ¿Hay alguna otra sección o detalle que te gustaría añadir?