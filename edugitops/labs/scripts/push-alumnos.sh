#!/usr/bin/env bash
set -euo pipefail

# 1. Definir la ubicación del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 2. Definir la raíz del proyecto (edugitops)
# Subimos 2 niveles: scripts -> labs -> edugitops
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 3. Cargar .env desde la raíz del proyecto
if [[ -f "${PROJECT_ROOT}/.env" ]]; then set -a; . "${PROJECT_ROOT}/.env"; set +a; fi

# 4. Definir la ruta del fichero alumnos.yaml
# NOTA: Según tu captura, está dentro de 'src'. Si decidiste dejarlo fuera, quita '/src'
ALUMNOS_FILE="${PROJECT_ROOT}/src/alumnos.yaml"

GIT_REMOTE="${GIT_REMOTE:-${GITEA_REMOTE_NAME:-gitea}}"
REMOTE_URL="${GITEA_REPO_URL:-}"

if [[ ! -f "${ALUMNOS_FILE}" ]]; then
  echo "Error: File ${ALUMNOS_FILE} not found." >&2
  exit 1
fi

# 5. Cambiamos al directorio raíz para ejecutar los comandos git
cd "${PROJECT_ROOT}"

git_status=$(git status --porcelain -- "${ALUMNOS_FILE}")
if [[ -z "${git_status}" ]]; then
  echo "No changes detected in ${ALUMNOS_FILE}." >&2
  exit 0
fi

git add "${ALUMNOS_FILE}"
commit_ts=$(date +%Y%m%d-%H%M)
commit_msg="alumno-${commit_ts}"
git commit -m "${commit_msg}"

# Configuración del remoto
if [[ -n "${REMOTE_URL}" ]]; then
  if git remote get-url "${GIT_REMOTE}" >/dev/null 2>&1; then
    git remote set-url "${GIT_REMOTE}" "${REMOTE_URL}"
  else
    git remote add "${GIT_REMOTE}" "${REMOTE_URL}"
  fi
fi

git push "${GIT_REMOTE}"

echo "Changes for ${ALUMNOS_FILE} pushed with commit ${commit_msg}."