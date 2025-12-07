#!/bin/bash
# Elimina todas las reglas del ruleset active_checks:httpv2 y aplica cambios en Checkmk.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -f "$ROOT_DIR/.env" ]]; then set -a; . "$ROOT_DIR/.env"; set +a; fi

set -euo pipefail

# --- CONFIGURACIÓN ---
CMK_BASE_URL="${CMK_BASE_URL:-${CHECKMK_URL:-http://127.0.0.1:5000/}}"
CMK_BASE_URL="${CMK_BASE_URL%/}"
CMK_SITE="${CMK_SITE:-${CHECKMK_SITE:-cmk}}"
API_USER="${API_USER:-${CHECKMK_API_USER:-cmkadmin}}"
API_SECRET="${API_SECRET:-${CHECKMK_API_SECRET:-admin123}}"

# --- ENDPOINTS Y CABECERAS ---
API_URL_V2="$CMK_BASE_URL/$CMK_SITE/check_mk/api/2.0"
API_URL_V1="$CMK_BASE_URL/$CMK_SITE/check_mk/api/1.0"
AUTH_HEADER_V2="Authorization: Basic $(echo -n "$API_USER:$API_SECRET" | base64)"
AUTH_HEADER_V1="Authorization: Bearer $API_USER $API_SECRET"
ACCEPT_HEADER="Accept: application/json"
CONTENT_TYPE="Content-Type: application/json"

command -v jq >/dev/null 2>&1 || { echo "Se requiere 'jq' para procesar la respuesta de la API."; exit 1; }

echo "--- [Paso 1] Listando reglas active_checks:httpv2 ---"
RULES_JSON=$(curl -sS -H "$ACCEPT_HEADER" -H "$AUTH_HEADER_V2" \
  "$API_URL_V2/domain-types/rule/collections/all?ruleset_name=active_checks:httpv2")

RULE_IDS=$(echo "$RULES_JSON" | jq -r '.value[]?.id // empty')

if [[ -z "$RULE_IDS" ]]; then
  echo "No se encontraron reglas para active_checks:httpv2. Nada que borrar."
  exit 0
fi

echo "Se encontraron las siguientes reglas: $(echo "$RULE_IDS" | tr '\n' ' ')"

echo "--- [Paso 2] Borrando reglas ---"
for rule_id in $RULE_IDS; do
  echo "Borrando regla $rule_id..."
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
    "$API_URL_V2/objects/rule/$rule_id" \
    -H "$ACCEPT_HEADER" \
    -H "$AUTH_HEADER_V2")

  if [[ "$STATUS" != "200" && "$STATUS" != "204" ]]; then
    echo "❌ Error al borrar $rule_id (HTTP $STATUS)."
    exit 1
  fi
done

echo "--- [Paso 3] Activando cambios ---"
PENDING_CHANGES_URL="$API_URL_V1/domain-types/activation_run/collections/pending_changes"

ETAG=$(curl -s -D - -o /dev/null -X GET "$PENDING_CHANGES_URL" \
  -H "$ACCEPT_HEADER" \
  -H "$AUTH_HEADER_V1" \
  | tr -d '\r' \
  | awk -F': ' 'tolower($1)=="etag"{print $2; exit}')

if [[ -z "${ETAG:-}" ]]; then
  ETAG="*"
fi

ACTIVATE_URL="$API_URL_V1/domain-types/activation_run/actions/activate-changes/invoke"

ACTIVATE_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$ACTIVATE_URL" \
  -H "$ACCEPT_HEADER" \
  -H "$CONTENT_TYPE" \
  -H "$AUTH_HEADER_V1" \
  -H "If-Match: $ETAG" \
  -d "{
        \"redirect\": false,
        \"force_foreign_changes\": false,
        \"sites\": [\"$CMK_SITE\"]
      }")

ACTIVATE_STATUS=$(echo "$ACTIVATE_RESPONSE" | tr -d '\n' | sed -e 's/.*HTTP_CODE://')

if [[ "$ACTIVATE_STATUS" -eq 200 ]] || [[ "$ACTIVATE_STATUS" -eq 201 ]] || [[ "$ACTIVATE_STATUS" -eq 204 ]]; then
  echo "✅ Cambios activados correctamente."
else
  echo "❌ Error activando cambios (Código $ACTIVATE_STATUS):"
  echo "$ACTIVATE_RESPONSE" | sed -e 's/HTTP_CODE:.*//g'
  exit 1
fi

echo "Proceso completado."
