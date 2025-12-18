#!/bin/bash
# NOMBRE: checkmk-crear-regla-tcp.sh
# DESCRIPCIÓN: Crea una regla de chequeo TCP activo en Checkmk.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -f "$ROOT_DIR/.env" ]]; then set -a; . "$ROOT_DIR/.env"; set +a; fi

set -u

# --- CONFIGURACIÓN ---
CMK_BASE_URL="${CMK_BASE_URL:-${CHECKMK_URL:-http://127.0.0.1:5000/}}"
CMK_BASE_URL="${CMK_BASE_URL%/}"
CMK_SITE="${CMK_SITE:-${CHECKMK_SITE:-cmk}}"
API_USER="${API_USER:-${CHECKMK_API_USER:-cmkadmin}}"
API_SECRET="${API_SECRET:-${CHECKMK_API_SECRET:-admin123}}"
SKIP_ACTIVATE="${SKIP_ACTIVATE:-0}"

# URL Base
API_URL="$CMK_BASE_URL/$CMK_SITE/check_mk/api/1.0"
AUTH_HEADER="Authorization: Bearer $API_USER $API_SECRET"
CONTENT_TYPE="Content-Type: application/json"
ACCEPT_HEADER="Accept: application/json"

# --- DATOS DE ENTRADA ---
# 1. El Host en Checkmk (donde se colgará el servicio)
TARGET_HOST_NAME="${1:-${TARGET_HOST_NAME:-}}"
# 2. La dirección DNS/IP real del servicio destino
TARGET_ADDRESS="${2:-${TARGET_ADDRESS:-}}"
# 3. El puerto TCP
TARGET_PORT="${3:-${TARGET_PORT:-}}"
# 4. El nombre que tendrá el servicio en Checkmk
SERVICE_NAME="${4:-${SERVICE_NAME:-}}"

if [[ -z "$TARGET_HOST_NAME" || -z "$TARGET_ADDRESS" || -z "$TARGET_PORT" || -z "$SERVICE_NAME" ]]; then
  echo "Uso: $0 <HOST_CHECKMK> <ADDRESS_DESTINO> <PUERTO> <NOMBRE_SERVICIO>"
  exit 1
fi

echo "--- Creando Regla TCP para $SERVICE_NAME ($TARGET_ADDRESS:$TARGET_PORT) ---"

# Construimos el payload JSON con cuidado de las comillas
RULE_PAYLOAD=$(cat <<EOF
{
  "ruleset": "active_checks:tcp",
  "folder": "/",
  "properties": {
    "description": "Monitorizar TCP $SERVICE_NAME",
    "disabled": false
  },  
  "value_raw": "{'port': $TARGET_PORT, 'svc_description': 'TCP $SERVICE_NAME', 'hostname': '$TARGET_ADDRESS'}",
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
    echo "✅ Regla TCP creada correctamente."
else
    echo "❌ Error creando regla TCP (Código $HTTP_STATUS):"
    echo "$HTTP_BODY"
    exit 1
fi

# La activación se delega al orquestador o se hace aquí si SKIP_ACTIVATE=0
if [[ "$SKIP_ACTIVATE" == "1" ]]; then
  exit 0
fi

