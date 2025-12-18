#!/bin/bash
# Elimina todas las reglas del ruleset active_checks:tcp

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

API_URL_V2="$CMK_BASE_URL/$CMK_SITE/check_mk/api/2.0"
AUTH_HEADER_V2="Authorization: Basic $(echo -n "$API_USER:$API_SECRET" | base64)"
ACCEPT_HEADER="Accept: application/json"

command -v jq >/dev/null 2>&1 || { echo "Se requiere 'jq'."; exit 1; }

echo "--- [TCP] Listando reglas active_checks:tcp ---"
RULES_JSON=$(curl -sS -H "$ACCEPT_HEADER" -H "$AUTH_HEADER_V2" \
  "$API_URL_V2/domain-types/rule/collections/all?ruleset_name=active_checks:tcp")

RULE_IDS=$(echo "$RULES_JSON" | jq -r '.value[]?.id // empty')

if [[ -z "$RULE_IDS" ]]; then
  echo "No se encontraron reglas TCP. Nada que borrar."
  exit 0
fi

for rule_id in $RULE_IDS; do
  echo "Borrando regla TCP $rule_id..."
  curl -s -o /dev/null -X DELETE \
    "$API_URL_V2/objects/rule/$rule_id" \
    -H "$ACCEPT_HEADER" \
    -H "$AUTH_HEADER_V2"
done

echo "✅ Reglas TCP eliminadas."