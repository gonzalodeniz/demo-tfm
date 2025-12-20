#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"
REPO_DIR="${2:-.}"

die() { echo "ERROR: $*" >&2; exit 1; }

# -----------------------------------------------------------------------------
# gitea_create_and_push.sh (Versión Corregida con Force Push)
# -----------------------------------------------------------------------------

# Carga .env
load_env() {
  [[ -f "$ENV_FILE" ]] || die "No existe el fichero de entorno: $ENV_FILE"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
}

require_vars() {
  local vars=(
    GITEA_URL
    GITEA_REPO_NAME
    GITEA_REMOTE_NAME
    GITEA_BRANCH
    GITEA_USER
    GITEA_PASSWORD
  )
  for v in "${vars[@]}"; do
    [[ -n "${!v:-}" ]] || die "Falta la variable $v en $ENV_FILE"
  done
}

derive_urls() {
  local base="${GITEA_URL%/}"
  GITEA_API_URL="${base}/api/v1"
  GITEA_REPO_URL="${base}/${GITEA_USER}/${GITEA_REPO_NAME}.git"
}

check_connectivity() {
  local url="${GITEA_URL%/}"
  echo "🔍 Comprobando conectividad con Gitea ($url)..."
  
  if ! curl -s --connect-timeout 3 "$url" >/dev/null; then
    echo "" >&2
    echo "❌ ERROR DE CONEXIÓN: No se puede acceder a $url" >&2
    echo "👉 SOLUCIÓN: Ejecuta 'make expose' en otra terminal." >&2
    echo "" >&2
    exit 1
  fi
}

url_with_creds() {
  local url="$1" user="$2" pass="$3"
  if [[ "$url" =~ ^(https?://)(.*)$ ]]; then
    echo "${BASH_REMATCH[1]}${user}:${pass}@${BASH_REMATCH[2]}"
  else
    echo "$url"
  fi
}

api_check_repo_exists() {
  local check_url="${GITEA_API_URL%/}/repos/${GITEA_USER}/${GITEA_REPO_NAME}"
  curl -sS -o /dev/null -w "%{http_code}" \
    -u "${GITEA_USER}:${GITEA_PASSWORD}" \
    "$check_url"
}

api_create_repo() {
  local create_url="${GITEA_API_URL%/}/user/repos"
  local payload
  payload=$(cat <<JSON
{
  "name": "${GITEA_REPO_NAME}",
  "private": false,
  "auto_init": false
}
JSON
)
  curl -sS -o /dev/null -w "%{http_code}" \
    -u "${GITEA_USER}:${GITEA_PASSWORD}" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    -X POST "$create_url"
}

ensure_git_repo_and_push() {
  cd "$REPO_DIR"

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git init
  fi

  git config user.name  >/dev/null 2>&1 || git config user.name  "${GITEA_USER}"
  git config user.email >/dev/null 2>&1 || git config user.email "${GITEA_USER}@local"

  if git rev-parse --verify "$GITEA_BRANCH" >/dev/null 2>&1; then
    git checkout "$GITEA_BRANCH"
  else
    git checkout -B "$GITEA_BRANCH"
  fi

  if git remote get-url "$GITEA_REMOTE_NAME" >/dev/null 2>&1; then
    git remote set-url "$GITEA_REMOTE_NAME" "$GITEA_REPO_URL"
  else
    git remote add "$GITEA_REMOTE_NAME" "$GITEA_REPO_URL"
  fi

  git add -A
  if git diff --cached --quiet; then
    echo "Sin cambios pendientes. Procediendo a push..."
  else
    git commit -m "Initial commit from script"
  fi

  local base_url
  base_url="$(git remote get-url "$GITEA_REMOTE_NAME")"
  local push_url
  push_url="$(url_with_creds "$base_url" "$GITEA_USER" "$GITEA_PASSWORD")"

  echo "🚀 Subiendo cambios a Gitea (Force Push)..."
  git remote set-url --push "$GITEA_REMOTE_NAME" "$push_url"
  
  # CAMBIO CLAVE: --force para sobreescribir cualquier historia divergente en Gitea
  git push -u --force "$GITEA_REMOTE_NAME" "$GITEA_BRANCH"

  git remote set-url --push "$GITEA_REMOTE_NAME" "$base_url"
}

main() {
  load_env
  require_vars
  derive_urls
  check_connectivity

  echo "GITEA_URL      = ${GITEA_URL%/}"
  
  local code
  code="$(api_check_repo_exists)"

  if [[ "$code" == "200" ]]; then
    echo "Repo ya existe. Actualizando..."
  elif [[ "$code" == "404" ]]; then
    echo "Repo no existe. Creándolo..."
    local create_code
    create_code="$(api_create_repo)"
    [[ "$create_code" == "201" || "$create_code" == "200" ]] || die "Error creando repo. HTTP $create_code"
  else
    die "Error comprobando repo. HTTP $code"
  fi

  ensure_git_repo_and_push
  echo "✅ Todo listo: Código subido correctamente."
}

main "$@"