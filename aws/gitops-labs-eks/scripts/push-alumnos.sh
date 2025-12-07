#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ALUMNOS_FILE="${REPO_DIR}/alumnos.yaml"
GIT_REMOTE="${GIT_REMOTE:-${GITEA_REMOTE_NAME:-gitea}}"

if [[ ! -f "${ALUMNOS_FILE}" ]]; then
  echo "File ${ALUMNOS_FILE} not found. Nothing to push." >&2
  exit 0
fi

cd "${REPO_DIR}"

git_status=$(git status --porcelain -- "${ALUMNOS_FILE}")
if [[ -z "${git_status}" ]]; then
  echo "No changes detected in ${ALUMNOS_FILE}." >&2
  exit 0
fi

git add -A "${ALUMNOS_FILE}"
commit_ts=$(date +%Y%m%d-%H%M)
commit_msg="alumno-${commit_ts}"
git commit -m "${commit_msg}"
git push "${GIT_REMOTE}"

echo "Changes for ${ALUMNOS_FILE} pushed with commit ${commit_msg}."
