#!/usr/bin/env bash
# Simple helper to create a host in Checkmk via REST API.
# No requiere parámetros; toma nombre/IP del host desde variables de entorno (p. ej. `.env`):
#   CHECKMK_HOST_NAME (obligatoria)
#   CHECKMK_HOST_IP   (opcional)

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
HOST_IP="${CHECKMK_HOST_IP:-${HOST_IP:-}}"

if [[ -z "${HOST_NAME}" ]]; then
  echo "Debes definir CHECKMK_HOST_NAME en el entorno (p. ej. en .env)." >&2
  exit 1
fi

JSON_PAYLOAD=$(cat <<EOF
{
  "folder": "/",
  "host_name": "${HOST_NAME}",
  "attributes": {
    "tag_agent": "no-agent"$( [[ -n "${HOST_IP}" ]] && echo ", \"ipaddress\": \"${HOST_IP}\"" )
  }
}
EOF
)

echo "Creando host '${HOST_NAME}' en ${CMK_BASE_URL} (site ${SITE})..."
curl -sS -u "${CMK_USER}:${CMK_PASSWORD}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Requested-By: cli" \
  -X POST "${API_V1}/domain-types/host_config/collections/all" \
  -d "${JSON_PAYLOAD}"
echo

ACTIVATE_PAYLOAD=$(cat <<EOF
{
  "sites": ["${SITE}"],
  "force_foreign_changes": false
}
EOF
)

PENDING_URL="${API_V1}/domain-types/activation_run/collections/pending_changes"

echo "Obteniendo ETag de pending changes..."
ETAG=$(curl -sS -u "${CMK_USER}:${CMK_PASSWORD}" \
  -H "Accept: application/json" \
  -D - -o /dev/null "${PENDING_URL}" | tr -d '\r' | awk '/^ETag:/ {gsub(/"/,"",$2); print $2; exit}')

if [[ -z "${ETAG}" ]]; then
  echo "No se pudo obtener el ETag para activar cambios (no hay cambios pendientes o falta cabecera ETag)." >&2
  exit 1
fi

echo "Activando cambios con If-Match: ${ETAG} ..."
curl -sS -u "${CMK_USER}:${CMK_PASSWORD}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Requested-By: cli" \
  -H "If-Match: ${ETAG}" \
  -X POST "${API_V1}/domain-types/activation_run/actions/activate-changes/invoke" \
  -d "${ACTIVATE_PAYLOAD}"
echo
