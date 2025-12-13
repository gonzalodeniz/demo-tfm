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


Aquí tienes la continuación del archivo `README.md`. Puedes añadir este contenido a continuación de la sección de Minikube que generamos antes.

He añadido los pasos críticos para subir la imagen a un registro (Docker Hub) y cómo obtener la URL pública del Load Balancer, que son las diferencias principales con respecto a la versión local.

-----

## ☁️ Despliegue en AWS EKS

Ejecutar la aplicación en un clúster real como EKS requiere un enfoque ligeramente diferente: la imagen Docker debe estar accesible en internet (Docker Hub o ECR) y el acceso se realiza mediante un Balanceador de Carga de AWS.

### Prerrequisitos EKS

  * Tener acceso configurado al clúster EKS (`aws eks update-kubeconfig ...`).
  * Una cuenta en [Docker Hub](https://hub.docker.com/) (o un repositorio ECR) para alojar la imagen.
  * Archivo necesario: `eks-deployment.yaml`.

### Pasos de Ejecución

#### 1\. Preparar y Subir la Imagen Docker

A diferencia de Minikube, EKS no puede leer las imágenes de tu ordenador. Debes subirlas a un registro.

1.  Inicia sesión en Docker Hub desde tu terminal:

    ```bash
    docker login
    ```

2.  Construye la imagen etiquetándola con tu nombre de usuario de Docker Hub:

    ```bash
    # Reemplaza 'tu_usuario' por tu usuario real de Docker Hub
    docker build -t tu_usuario/flask-k8s-client:v1 .
    ```

3.  Sube la imagen a la nube:

    ```bash
    docker push tu_usuario/flask-k8s-client:v1
    ```

#### 2\. Actualizar el Manifiesto

Antes de desplegar, debes indicar a Kubernetes dónde descargar tu imagen.

1.  Abre el archivo `eks-deployment.yaml`.
2.  Busca la línea `image:` dentro de la sección `Deployment`.
3.  Cámbiala por la imagen que acabas de subir:
    ```yaml
    containers:
      - name: flask
        image: tu_usuario/flask-k8s-client:v1  # <--- Tu imagen aquí
        imagePullPolicy: Always
    ```

#### 3\. Desplegar en el Clúster

Aplica la configuración. Esto creará la cuenta de servicio (ServiceAccount), los roles de lectura (RBAC), el Pod y solicitará un Balanceador de Carga a AWS.

```bash
kubectl apply -f eks-deployment.yaml
```

#### 4\. Obtener la URL Pública

La creación del Load Balancer en AWS puede tardar unos minutos (entre 2 y 5 minutos).

Ejecuta el siguiente comando para ver el estado:

```bash
kubectl get svc flask-k8s-service-lb
```

  * Si en la columna `EXTERNAL-IP` ves `<pending>`, espera unos segundos y vuelve a ejecutar el comando.
  * Cuando veas una dirección larga (ej: `a43...us-east-1.elb.amazonaws.com`), esa es tu dirección pública.

Copia esa dirección `EXTERNAL-IP` y pégala en tu navegador. Añade `/services` al final para ver el listado de servicios de tu clúster EKS.

-----

### ⚠️ Limpieza (Importante para AWS)

Los Load Balancers en AWS tienen un coste (o consumen créditos). Cuando termines tus pruebas en EKS, elimina los recursos para detener la facturación:

```bash
kubectl delete -f eks-deployment.yaml
```

Esto eliminará el Pod y borrará automáticamente el Load Balancer de AWS.

## EduGitOps - Gestor de Laboratorios Virtuales

Este proyecto es un prototipo funcional para un Trabajo de Fin de Máster (TFM) orientado al despliegue de laboratorios educativos mediante **GitOps**.

La aplicación es una interfaz web desarrollada en **Python (Flask)** que permite a docentes gestionar de forma visual la asignación de herramientas (Prometheus, Grafana, JupyterHub, etc.) a los alumnos. Su objetivo es abstraer la complejidad de editar manualmente archivos YAML, facilitando la integración con **ArgoCD** para el despliegue automático en Kubernetes.

### 🚀 Características Actuales

* **Lectura de Datos:** Carga automática de alumnos y catálogo de servicios desde archivos YAML (`alumnos.yaml` y `catalogo-servicios.yaml`).
* **Interfaz Visual:** Diseño intuitivo basado en Bootstrap 5 que replica un panel de control profesional.
* **Visualización de Estado:** Muestra qué laboratorios tiene asignados cada alumno.
* **Diseño Responsive:** Adaptable a dispositivos móviles y escritorio.
* **Simulación de GitOps:** Interfaz preparada para simular el flujo de Commit & Push (funcionalidad visual).

### 📋 Requisitos Previos

* Python 3.x instalado.
* Git (opcional, para clonar el repositorio).

### 🛠️ Instalación y Configuración

Debido a las políticas de seguridad de los sistemas operativos modernos (PEP 668), es necesario utilizar un **entorno virtual** para instalar las dependencias y evitar el error `externally-managed-environment`.

Sigue estos pasos en tu terminal:

#### 1. Preparar el proyecto
Asegúrate de tener la siguiente estructura de archivos en tu carpeta:
```text
/tfm-edugitops
├── app.py
├── alumnos.yaml
├── catalogo-servicios.yaml
├── requirements.txt
├── README.md
├── static/
│   └── style.css
└── templates/
    └── index.html
```

#### 2. Crear y activar el Entorno Virtual (Venv)
En Linux / macOS:

```Bash

# Crear el entorno virtual llamado 'venv'
python3 -m venv venv

# Activar el entorno
source venv/bin/activate
```
En Windows:

```Bash

# Crear el entorno
python -m venv venv

# Activar el entorno
venv\Scripts\activate
```

Verás que el prompt de tu terminal cambia indicando (venv). Esto significa que estás dentro del entorno aislado.

#### 3. Instalar Dependencias
Una vez activo el entorno virtual, instala las librerías necesarias (Flask y PyYAML):

```Bash

pip install -r requirements.txt
```
(Si no tienes el archivo requirements.txt, puedes crearlo con el contenido: Flask y PyYAML, o instalar manualmente con pip install Flask PyYAML).

### ▶️ Ejecución
Asegúrate de que el entorno virtual sigue activo y ejecuta:

```Bash
python app.py
```
Deberías ver una salida similar a:

```text

 * Serving Flask app 'app'
 * Debug mode: on
 * Running on [http://127.0.0.1:5000](http://127.0.0.1:5000)
```

Abre tu navegador web y visita: http://127.0.0.1:5000

### 📂 Estructura del Proyecto
app.py: Lógica del servidor Flask. Carga los YAML y renderiza la plantilla.

templates/index.html: La estructura HTML de la página usando Jinja2 y Bootstrap.

static/style.css: Estilos personalizados para ajustar la apariencia visual.

*.yaml: Archivos de datos que actúan como base de datos del sistema.

### 🐛 Solución de Problemas
Error: error: externally-managed-environment Si ves este error, es porque intentaste ejecutar pip install directamente en el sistema sin un entorno virtual. Asegúrate de ejecutar el paso 2 de la instalación (source venv/bin/activate) antes de instalar nada.

Error: FileNotFoundError La aplicación busca alumnos.yaml y catalogo-servicios.yaml en la carpeta raíz. Asegúrate de que los archivos existen y tienen el nombre correcto.

Debido a las políticas de seguridad de los sistemas operativos modernos (PEP 668), es necesario utilizar un **entorno virtual** para instalar las dependencias y evitar el error `externally-managed-environment`.
