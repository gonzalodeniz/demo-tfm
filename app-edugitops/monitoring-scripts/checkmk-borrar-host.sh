#!/usr/bin/env bash
# Borra un host en Checkmk usando la variable CHECKMK_HOST_NAME definida en .env.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -f "$ROOT_DIR/.env" ]]; then set -a; . "$ROOT_DIR/.env"; set +a; fi

set -euo pipefail

CMK_BASE_URL="${CMK_BASE_URL:-${CHECKMK_URL:-http://127.0.0.1:5000/}}"
CMK_BASE_URL="${CMK_BASE_URL%/}"
SITE="${SITE:-${CHECKMK_SITE:-cmk}}"
CMK_USER="${CMK_USER:-${CHECKMK_API_USER:-cmkadmin}}"
CMK_PASSWORD="${CMK_PASSWORD:-${CHECKMK_API_SECRET:-admin123}}"
API_V1="$CMK_BASE_URL/$SITE/check_mk/api/1.0"

HOST_NAME="${CHECKMK_HOST_NAME:-${HOST_NAME:-}}"

if [[ -z "${HOST_NAME}" ]]; then
  echo "Debes definir CHECKMK_HOST_NAME en el entorno (p. ej. en .env)." >&2
  exit 1
fi

DELETE_URL="${API_V1}/objects/host_config/${HOST_NAME}"

echo "Borrando host '${HOST_NAME}' en ${CMK_BASE_URL} (site ${SITE})..."
curl -sS -u "${CMK_USER}:${CMK_PASSWORD}" \
  -H "Accept: application/json" \
  -X DELETE "${DELETE_URL}"
echo

echo "Activando cambios pendientes..."
ETAG=$(curl -s -D - -o /dev/null -u "${CMK_USER}:${CMK_PASSWORD}" \
  -H "Accept: application/json" \
  "${API_V1}/domain-types/activation_run/collections/pending_changes" \
  | tr -d '\r' \
  | awk -F': ' 'tolower($1)=="etag"{print $2; exit}')

if [[ -z "${ETAG}" ]]; then
  ETAG="*"
fi

curl -sS -u "${CMK_USER}:${CMK_PASSWORD}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "If-Match: ${ETAG}" \
  -X POST "${API_V1}/domain-types/activation_run/actions/activate-changes/invoke" \
  -d "{
        \"redirect\": false,
        \"force_foreign_changes\": false,
        \"sites\": [\"${SITE}\"]
      }"
echo
