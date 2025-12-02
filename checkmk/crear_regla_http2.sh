#!/bin/bash
# NOMBRE: crear_regla_http.sh

set -u

# --- CONFIGURACIÓN ---
CMK_SITE="cmk"
CMK_SERVER="127.0.0.1:5000"
API_USER="cmkadmin"
API_SECRET="admin123"

# URL Base
API_URL="http://$CMK_SERVER/$CMK_SITE/check_mk/api/1.0"
AUTH_HEADER="Authorization: Bearer $API_USER $API_SECRET"
CONTENT_TYPE="Content-Type: application/json"
ACCEPT_HEADER="Accept: application/json"

# --- DATOS DE LA MONITORIZACIÓN ---
# Parametrización obligatoria vía argumentos o variables de entorno.
TARGET_HOST_NAME="${1:-${TARGET_HOST_NAME:-}}"
TARGET_URL="${2:-${TARGET_URL:-}}"
SERVICE_NAME="${3:-${SERVICE_NAME:-}}"

if [[ -z "$TARGET_HOST_NAME" || -z "$TARGET_URL" || -z "$SERVICE_NAME" ]]; then
  echo "Uso: $0 <TARGET_HOST_NAME> <TARGET_URL> <SERVICE_NAME>"
  echo "También puedes exportar TARGET_HOST_NAME, TARGET_URL y SERVICE_NAME."
  echo "Ejemplo: TARGET_HOST_NAME=host1 TARGET_URL=https://example.com SERVICE_NAME=\"Check Example\" $0"
  exit 1
fi

echo "--- [Paso 1] Creando Regla HTTP para $TARGET_HOST_NAME ---"

RULE_PAYLOAD=$(cat <<EOF
{
  "ruleset": "active_checks:httpv2",
  "folder": "/",
  "properties": {
    "description": "Monitorizar $SERVICE_NAME",
    "disabled": false
  },  
  "value_raw": "{'endpoints': [{'service_name': {'prefix': 'auto', 'name': '$SERVICE_NAME'}, 'url': '$TARGET_URL'}], 'standard_settings': {}}",
  "conditions": {
    "host_name": {
        "match_on": ["$TARGET_HOST_NAME"],
        "operator": "one_of"
    }
  }
}
EOF
)

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$API_URL/domain-types/rule/collections/all" \
  -H "$ACCEPT_HEADER" \
  -H "$CONTENT_TYPE" \
  -H "$AUTH_HEADER" \
  -d "$RULE_PAYLOAD")

HTTP_STATUS=$(echo "$RESPONSE" | tr -d '\n' | sed -e 's/.*HTTP_CODE://')
HTTP_BODY=$(echo "$RESPONSE" | sed -e 's/HTTP_CODE:.*//g')

if [[ "$HTTP_STATUS" -eq 200 ]] || [[ "$HTTP_STATUS" -eq 201 ]] || [[ "$HTTP_STATUS" -eq 204 ]]; then
    echo "✅ Regla creada correctamente."
else
    echo "❌ Error creando regla (Código $HTTP_STATUS):"
    echo "$HTTP_BODY"
    exit 1
fi

echo -e "\n--- [Paso 2] Activando Cambios ---"

# 2.1) Obtener ETag de pending changes (viene en cabeceras)
PENDING_CHANGES_URL="$API_URL/domain-types/activation_run/collections/pending_changes"

ETAG=$(curl -s -D - -o /dev/null -X GET "$PENDING_CHANGES_URL" \
  -H "$ACCEPT_HEADER" \
  -H "$AUTH_HEADER" \
  | tr -d '\r' \
  | awk -F': ' 'tolower($1)=="etag"{print $2; exit}')

# Fallback: si no se pudo leer, usar comodín
if [[ -z "${ETAG:-}" ]]; then
  ETAG="*"
fi

ACTIVATE_URL="$API_URL/domain-types/activation_run/actions/activate-changes/invoke"

ACTIVATE_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$ACTIVATE_URL" \
  -H "$ACCEPT_HEADER" \
  -H "$CONTENT_TYPE" \
  -H "$AUTH_HEADER" \
  -H "If-Match: $ETAG" \
  -d "{
        \"redirect\": false,
        \"force_foreign_changes\": false,
        \"sites\": [\"$CMK_SITE\"]
      }")

ACTIVATE_STATUS=$(echo "$ACTIVATE_RESPONSE" | tr -d '\n' | sed -e 's/.*HTTP_CODE://')

if [[ "$ACTIVATE_STATUS" -eq 200 ]] || [[ "$ACTIVATE_STATUS" -eq 201 ]] || [[ "$ACTIVATE_STATUS" -eq 204 ]]; then
    echo "✅ Cambios activados correctamente. Revisa el panel de Checkmk."
else
    echo "❌ Error activando cambios (Código $ACTIVATE_STATUS):"
    echo "$ACTIVATE_RESPONSE" | sed -e 's/HTTP_CODE:.*//g'
fi
exit 0
