# Checkmk en Minikube

Checkmk es una plataforma de monitorización IT (infra, apps, red) con servidor central y agentes. Aquí se despliega la edición RAW (cre) 2.4.0p16 sobre Minikube usando el contenedor oficial.

## Despliegue
- Con Makefile: `make apply`
- O manual: `kubectl apply -f checkmk.yaml`

Recursos creados en el namespace `checkmk`:
- PVC `checkmk-data` (10Gi en StorageClass `standard`)
- Deployment `checkmk` (1 réplica, `CMK_SITE_ID=cmk`)
- Service `checkmk` (NodePort 30500 para HTTP, 30657 para livestatus)

## Acceso web
- NodePort: `http://$(minikube ip):30500/`
- Port-forward (opcional): `make port-forward` y abrir `http://localhost:5000/`

## Login inicial
- Usuario: `cmkadmin`
- Contraseña: `cmkadmin` (valores por defecto de la imagen RAW)

## Borrado
- Con Makefile: `make delete-namespace`
- O manual: `kubectl delete namespace checkmk`

## Notas
- Si necesitas otra StorageClass, edita `checkmk.yaml` en el PVC.
- Ajusta los NodePorts si están ocupados en tu Minikube. Para que los asigne automáticamente, elimina las claves `nodePort` en el Service.
