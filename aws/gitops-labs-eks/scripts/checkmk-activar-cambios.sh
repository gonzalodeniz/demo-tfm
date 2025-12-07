#!/bin/bash
# Activa cambios pendientes en Checkmk (HTTP API v1) con fallback de ETag.

set -euo pipefail

# --- CONFIGURACIÓN ---
CMK_BASE_URL="${CMK_BASE_URL:-${CHECKMK_URL:-http://127.0.0.1:5000/}}"
CMK_BASE_URL="${CMK_BASE_URL%/}"
CMK_SITE="${CMK_SITE:-${CHECKMK_SITE:-cmk}}"
API_USER="${API_USER:-${CHECKMK_API_USER:-cmkadmin}}"
API_SECRET="${API_SECRET:-${CHECKMK_API_SECRET:-admin123}}"

API_URL="$CMK_BASE_URL/$CMK_SITE/check_mk/api/1.0"
AUTH_HEADER="Authorization: Bearer $API_USER $API_SECRET"
ACCEPT_HEADER="Accept: application/json"
CONTENT_TYPE="Content-Type: application/json"

PENDING_CHANGES_URL="$API_URL/domain-types/activation_run/collections/pending_changes"

ETAG=$(curl -s -D - -o /dev/null -X GET "$PENDING_CHANGES_URL" \
  -H "$ACCEPT_HEADER" \
  -H "$AUTH_HEADER" \
  | tr -d '\r' \
  | awk -F': ' 'tolower($1)=="etag"{print $2; exit}')

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
