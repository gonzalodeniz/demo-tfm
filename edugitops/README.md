# AWS - EKS
## Preparación del entorno

### Credenciales
Fichero de credenciales:
~/.aws/credentials

```
[default]
aws_access_key_id = TU_ACCESS_KEY
aws_secret_access_key = TU_SECRET_KEY
aws_session_token = TU_TOKEN
```

Ejemplo de ~/.aws/config:

```
[default]
region = us-east-1
ioutput = json
```

#### AWS CLI
Instalación de AWS CLI
```
# Descargar el instalador
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"

# Instalar unzip si no lo tienes
sudo apt update
sudo apt install unzip -y

# Descomprimir
unzip awscliv2.zip

# Instalar
sudo ./aws/install

# Verificar la instalación
aws --version
```

Fuentes de la instalación de AWS CLI:

Documentación oficial de AWS CLI v2 (instalación Linux):
https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

Ubicación de archivos de configuración de AWS CLI:
https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html


### EKSCTL
Instalación de eksctl
```
# Descargar eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp

# Mover a directorio del sistema
sudo mv /tmp/eksctl /usr/local/bin

# Verificar instalación
eksctl version
```
Fuente:
https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html

Crear un clúster:
https://eksctl.io/usage/creating-and-managing-clusters/

Configuración vía YAML:
https://eksctl.io/usage/schema/


## Creación del EKS

Crear (da problemas luego al borrar el cluster)
```
eksctl create cluster -f cluster.yaml
```

Borrar (no borra todos los componentes correctamente)
```
eksctl delete cluster -f cluster.yaml
```

Ver los clústeres EKS con eksctl
```
eksctl get cluster --region us-east-1
```

Ver detalles de un cluster
```
eksctl get cluster --name eks-unir-tfm --region us-east-1
```

Nodegroups de un cluster
```
eksctl get nodegroup --cluster cluster-unir-tfm --region us-east-1
```

Ver los stack creados
```
aws cloudformation describe-stacks --region us-east-1 \
  --stack-name eksctl-eks-unir-tfm-cluster
```

Activar el contexto del cluster EKS
```
 aws eks update-kubeconfig --region us-east-1 --name eks-unir-tfm
```


## Instalar ArgoCD
Crea el namespace e instala ArgoCD
```
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Comprueba que los pods arrancan
```
kubectl get pods -n argocd
```

ArgoCD instala el servidor como ClusterIP, así que debes cambiarlo a tipo LoadBalancer para acceder desde fuera en EKS:

```
kubectl patch svc argocd-server -n argocd \
  -p '{"spec": {"type": "LoadBalancer"}}'
```

Comprobar:
```
kubectl get svc -n argocd
```

Ver la IP pública de ArgoCD
```
kubectl get svc argocd-server -n argocd
```

Usuario y contraseña de acceso
```
# Usuario
admin

# Ver la contraseña
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 --decode; echo
```

### ArgoCD CLI
Instalación ArgoCD CLI
`` 
sudo curl -sSL -o /usr/local/bin/argocd \
https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64

sudo chmod +x /usr/local/bin/argocd
```

Configurar ARGOCD-CLI para que apunte a AWS:
```
ARGOCD_SERVER=afb25c2285d5c4109bb26eccd1d8b453-1056227366.us-east-1.elb.amazonaws.com
ARGOCD_SECRET=tUmCng-r5W0HTk4a
argocd login $ARGOCD_SERVER --username admin --password $ARGOCD_SECRET --grpc-web
```

Verifica la conexión
```
argocd version
```


### GITEA
Antes de aplicar el manifiesto, verifica que tengas el EBS CSI Driver instalado (es obligatorio para provisionar volúmenes EBS en EKS):


Desplegar Gitea en AWS
```
kubectl apply -f gitea.yaml
```

Comprobar servicios de Gitea
```
kubectl get services -n gitea
```

Cambiar el tipo de servicio a LoadBalancer
```
kubectl patch svc gitea -n gitea \
  -p '{"spec": {"type": "LoadBalancer"}}'
```

Verifica el cambio
```
kubectl get svc -n gitea
```

## Despliegue rápido con Makefile
En este directorio puedes usar el Makefile para desplegar los componentes en el clúster configurado en tu kubeconfig:
```
make argocd    # Despliega ArgoCD (usa el script provision/argocd-eks.sh)
make gitea     # Aplica provision/gitea-eks.yaml
make checkmk   # Aplica provision/checkmk-eks.yaml
make apps      # Ejecuta argocd, gitea y checkmk en orden
```


