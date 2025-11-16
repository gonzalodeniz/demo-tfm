#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${REPO_DIR}/alumnos"

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "Directory ${TARGET_DIR} not found. Nothing to push." >&2
  exit 1
fi

cd "${REPO_DIR}"

git_status=$(git status --porcelain -- "${TARGET_DIR}")
if [[ -z "${git_status}" ]]; then
  echo "No changes detected in ${TARGET_DIR}." >&2
  exit 0
fi

git add -A "${TARGET_DIR}"
commit_ts=$(date +%Y%m%d-%H%M)
commit_msg="alumno-${commit_ts}"
git commit -m "${commit_msg}"
git push

echo "Changes under ${TARGET_DIR} pushed with commit ${commit_msg}."
