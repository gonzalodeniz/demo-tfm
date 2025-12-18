#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${1:-.env}"
REPO_DIR="${2:-.}"

die() { echo "ERROR: $*" >&2; exit 1; }

# -----------------------------------------------------------------------------
# gitea_create_and_push.sh
#
# Descripción:
#   Automatiza la creación de un repositorio en Gitea y el envío (git push) del
#   contenido local a una rama específica.
#
#   Importante:
#     - Este script SOLO usa GITEA_URL para construir:
#         * GITEA_API_URL  = ${GITEA_URL}/api/v1
#         * GITEA_REPO_URL = ${GITEA_URL}/${GITEA_USER}/${GITEA_REPO_NAME}.git
#     - Si en el .env existen GITEA_API_URL o GITEA_REPO_URL, se IGNORAN.
#     - Esto es útil cuando ejecutas el script fuera del clúster (ej: localhost:3000
#       vía port-forward) y no puedes resolver dominios .svc.cluster.local.
#
# Uso:
#   ./gitea_create_and_push.sh [RUTA_ENV] [DIRECTORIO_REPO]
#
# Ejemplos:
#   ./scripts/gitea_create_and_push.sh
#   ./scripts/gitea_create_and_push.sh .env .
#
# Nota de seguridad:
#   Para evitar prompts de autenticación, el script construye temporalmente una
#   push-url con "usuario:password@" (solo para el push) y luego la limpia.
# -----------------------------------------------------------------------------

# Carga .env (formato KEY=VALUE)
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
  # Normaliza quitando "/" final
  local base="${GITEA_URL%/}"

  # Derivadas (se fuerzan siempre)
  GITEA_API_URL="${base}/api/v1"
  GITEA_REPO_URL="${base}/${GITEA_USER}/${GITEA_REPO_NAME}.git"
}

# Inserta credenciales en una URL http(s) para evitar prompts en git push
# OJO: si tu pass tiene caracteres raros (@, :, etc.), mejor token o credential helper.
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

  # Init si no es repo git
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git init
  fi

  # Config mínima para commitear si no está
  git config user.name  >/dev/null 2>&1 || git config user.name  "${GITEA_USER}"
  git config user.email >/dev/null 2>&1 || git config user.email "${GITEA_USER}@local"

  # Rama
  if git rev-parse --verify "$GITEA_BRANCH" >/dev/null 2>&1; then
    git checkout "$GITEA_BRANCH"
  else
    git checkout -B "$GITEA_BRANCH"
  fi

  # Remote (add o set-url) usando la URL derivada de GITEA_URL
  if git remote get-url "$GITEA_REMOTE_NAME" >/dev/null 2>&1; then
    git remote set-url "$GITEA_REMOTE_NAME" "$GITEA_REPO_URL"
  else
    git remote add "$GITEA_REMOTE_NAME" "$GITEA_REPO_URL"
  fi

  # Stage + commit si hay cambios
  git add -A
  if git diff --cached --quiet; then
    echo "No hay cambios para commitear. Haré push igualmente (por si ya había commits)."
  else
    git commit -m "Initial commit"
  fi

  # Push sin pedir credenciales (mete user/pass en la URL SOLO para push)
  local base_url
  base_url="$(git remote get-url "$GITEA_REMOTE_NAME")"
  local push_url
  push_url="$(url_with_creds "$base_url" "$GITEA_USER" "$GITEA_PASSWORD")"

  # Set push-url temporal y empuja
  git remote set-url --push "$GITEA_REMOTE_NAME" "$push_url"
  git push -u "$GITEA_REMOTE_NAME" "$GITEA_BRANCH"

  # Limpia push-url (vuelve a dejarlo como estaba)
  git remote set-url --push "$GITEA_REMOTE_NAME" "$base_url"
}

main() {
  load_env
  require_vars
  derive_urls

  echo "GITEA_URL      = ${GITEA_URL%/}"
  echo "GITEA_API_URL  = $GITEA_API_URL"
  echo "GITEA_REPO_URL = $GITEA_REPO_URL"
  echo "Comprobando repo ${GITEA_USER}/${GITEA_REPO_NAME} en Gitea (API)..."

  local code
  code="$(api_check_repo_exists)"

  if [[ "$code" == "200" ]]; then
    echo "Repo ya existe. Continuando con git push..."
  elif [[ "$code" == "404" ]]; then
    echo "Repo no existe. Creándolo..."
    local create_code
    create_code="$(api_create_repo)"
    [[ "$create_code" == "201" || "$create_code" == "200" ]] || die "No pude crear el repo. HTTP $create_code"
    echo "Repo creado."
  else
    die "No pude comprobar el repo. HTTP $code (revisa GITEA_URL/GITEA_USER/GITEA_PASSWORD)"
  fi

  ensure_git_repo_and_push
  echo "OK: push hecho a ${GITEA_REMOTE_NAME}/${GITEA_BRANCH}"
}

main "$@"
