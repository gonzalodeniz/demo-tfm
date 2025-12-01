#!/usr/bin/env bash
set -euo pipefail

# Simple helper to create a host in Checkmk via REST API.
# Uso: CMK_URL=http://localhost:5000 SITE=cmk ./create_host.sh <host_name> [ipaddress]

CMK_URL="${CMK_URL:-http://localhost:5000}"
SITE="${SITE:-cmk}"
CMK_USER="${CMK_USER:-cmkadmin}"
CMK_PASSWORD="${CMK_PASSWORD:-admin123}"

HOST_NAME="${1:-}"
HOST_IP="${2:-}"

if [[ -z "${HOST_NAME}" ]]; then
  echo "Usage: CMK_URL=http://localhost:5000 SITE=cmk $0 <host_name> [ipaddress]" >&2
  exit 1
fi

JSON_PAYLOAD=$(cat <<EOF
{
  "folder": "/",
  "host_name": "${HOST_NAME}",
  "attributes": {
    $( [[ -n "${HOST_IP}" ]] && echo "\"ipaddress\": \"${HOST_IP}\"" )
  }
}
EOF
)

echo "Creando host '${HOST_NAME}' en ${CMK_URL} (site ${SITE})..."
curl -sS -u "${CMK_USER}:${CMK_PASSWORD}" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -H "X-Requested-By: cli" \
  -X POST "${CMK_URL}/${SITE}/check_mk/api/1.0/domain-types/host_config/collections/all" \
  -d "${JSON_PAYLOAD}"
echo

ACTIVATE_PAYLOAD=$(cat <<EOF
{
  "sites": ["${SITE}"],
  "force_foreign_changes": false
}
EOF
)

PENDING_URL="${CMK_URL}/${SITE}/check_mk/api/1.0/domain-types/activation_run/collections/pending_changes"

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
  -X POST "${CMK_URL}/${SITE}/check_mk/api/1.0/domain-types/activation_run/actions/activate-changes/invoke" \
  -d "${ACTIVATE_PAYLOAD}"
echo
