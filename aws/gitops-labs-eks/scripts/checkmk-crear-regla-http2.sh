#!/bin/bash
# NOMBRE: crear_regla_http.sh

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

# --- DATOS DE LA MONITORIZACIÓN ---
# Parametrización obligatoria vía argumentos o variables de entorno.
TARGET_HOST_NAME="${1:-${TARGET_HOST_NAME:-}}"
TARGET_URL="${2:-${TARGET_URL:-}}"
SERVICE_NAME="${3:-${SERVICE_NAME:-}}"

if [[ -z "$TARGET_HOST_NAME" || -z "$TARGET_URL" || -z "$SERVICE_NAME" ]]; then
  echo ""
  echo "Uso:"
  echo "  $0 <TARGET_HOST_NAME> <TARGET_URL> <SERVICE_NAME>"
  echo ""
  echo "Descripción:"
  echo "  Crea una regla HTTP (HTTPv2) en Checkmk utilizando la API REST."
  echo ""
  echo "Parámetros obligatorios:"
  echo "  TARGET_HOST_NAME   Nombre del host en Checkmk."
  echo "  TARGET_URL         URL completa que será monitorizada."
  echo "  SERVICE_NAME       Nombre del servicio HTTP a crear."
  echo ""
  echo "Alternativa:"
  echo "  Puedes exportar las variables de entorno requeridas:"
  echo "  export TARGET_HOST_NAME=host1"
  echo "  export TARGET_URL=https://example.com"
  echo "  export SERVICE_NAME=\"Check Example\""
  echo "  $0"
  echo ""
  echo "Ejemplo completo:"
  echo "  $0 host1 https://example.com \"Check Example\""
  echo ""
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

# Permite omitir la activación cuando se use en lotes.
if [[ "$SKIP_ACTIVATE" == "1" || "$SKIP_ACTIVATE" == "true" ]]; then
  echo "Saltando activación (SKIP_ACTIVATE=$SKIP_ACTIVATE)."
  exit 0
fi

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

if [[ "$ACTIVATE_STATUS" -eq 412 ]]; then
  echo "⚠️  ETag no coincide (412). Reintentando activación con comodín..."
  ACTIVATE_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$ACTIVATE_URL" \
    -H "$ACCEPT_HEADER" \
    -H "$CONTENT_TYPE" \
    -H "$AUTH_HEADER" \
    -H "If-Match: *" \
    -d "{
          \"redirect\": false,
          \"force_foreign_changes\": false,
          \"sites\": [\"$CMK_SITE\"]
        }")
  ACTIVATE_STATUS=$(echo "$ACTIVATE_RESPONSE" | tr -d '\n' | sed -e 's/.*HTTP_CODE://')
fi

if [[ "$ACTIVATE_STATUS" -eq 200 ]] || [[ "$ACTIVATE_STATUS" -eq 201 ]] || [[ "$ACTIVATE_STATUS" -eq 204 ]]; then
  echo "✅ Cambios activados correctamente. Revisa el panel de Checkmk."
  exit 0
else
  echo "❌ Error activando cambios (Código $ACTIVATE_STATUS):"
  echo "$ACTIVATE_RESPONSE" | sed -e 's/HTTP_CODE:.*//g'
  exit 1
fi
