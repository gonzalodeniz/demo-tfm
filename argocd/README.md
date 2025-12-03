# Argo CD - utilidades rápidas

Makefile con atajos para instalar Argo CD, obtener la contraseña inicial, hacer login por CLI y exponer el servidor vía port-forward.

## Requisitos
- `kubectl` apuntando al clúster correcto.
- Acceso a Internet para aplicar los manifiestos oficiales.
- `argocd` CLI instalada para el login.

## Opciones del Makefile
- `make help`: muestra las opciones disponibles.
- `make install`: crea el namespace `argocd` e instala Argo CD con los manifiestos oficiales (`stable/manifests/install.yaml`).
- `make password`: muestra la contraseña inicial (`argocd-initial-admin-secret`) ya decodificada.
- `make login`: inicia sesión contra `localhost:8080` con usuario `admin` y contraseña `1q2w3e4R.` usando `--insecure`.
- `make expose`: ejecuta `kubectl port-forward svc/argocd-server -n argocd 8080:443` en segundo plano, guardando PID en `/tmp/argocd-port-forward.pid` y log en `/tmp/argocd-port-forward.log`. Deténlo con `kill $(cat /tmp/argocd-port-forward.pid)`.

## Notas
- La contraseña por defecto se lee del secreto; si la cambiaste, actualiza el comando de `login`.
- El port-forward queda activo hasta que mates el proceso; revisa el log para errores de conexión.
