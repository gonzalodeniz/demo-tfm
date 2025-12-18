#!/bin/bash
set -e # Detener si hay error

echo "🚀 Desplegando app-edugitops con configuración extendida..."

# Cargar variables del .env
if [ -f .env ]; then
    set -a; source .env; set +a
else
    echo "❌ Error: No se encuentra el fichero .env"
    exit 1
fi

# Sustituir variables y aplicar
envsubst '$APP_IMAGE $APP_VERSION $GITEA_API_URL $GITEA_REPO_NAME $GITEA_BRANCH $GITEA_FILE_PATH $GITEA_CATALOGO_PATH $GITEA_USER $GITEA_PASSWORD $FLASK_DEBUG $CHECKMK_API_USER $CHECKMK_API_SECRET $CHECKMK_SITE $CHECKMK_HOST_NAME $CHECKMK_URL $CHECKMK_HOST_IP' < ./stack/app-edugitops.yaml | kubectl apply -f -

echo "✅ App desplegada."