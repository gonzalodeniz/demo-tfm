#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

APP_NAME="${APP_NAME:-alumnos-monitoring}"
APP_NAMESPACE="${APP_NAMESPACE:-argocd}"
NAMESPACE_PREFIX="${NAMESPACE_PREFIX:-monitoring}"
POD_TIMEOUT="${POD_TIMEOUT:-600}"
POD_CHECK_INTERVAL="${POD_CHECK_INTERVAL:-5}"
REQUIRED_APPS=("grafana" "prometheus")
LOG_FILE="${LOG_FILE:-${REPO_DIR}/tiempo-monitoring.csv}"

LAST_NAMESPACE_COUNT=0

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

run_with_timer() {
  local label=$1
  shift
  local start end duration
  log "Iniciando ${label}..."
  start=$(date +%s)
  "$@"
  end=$(date +%s)
  duration=$((end - start))
  log "${label} completado en ${duration} segundos."
}

pods_ready_in_namespace() {
  local namespace=$1
  local pending=0

  for app in "${REQUIRED_APPS[@]}"; do
    mapfile -t pod_lines < <(kubectl get pods -n "${namespace}" -l "app=${app}" \
      -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.phase}{"\n"}{end}' 2>/dev/null || true)

    if (( ${#pod_lines[@]} == 0 )); then
      log "Namespace ${namespace}: no se han encontrado pods de ${app}."
      pending=1
      continue
    fi

    for line in "${pod_lines[@]}"; do
      local pod phase
      pod=$(awk '{print $1}' <<<"${line}")
      phase=$(awk '{print $2}' <<<"${line}")
      if [[ "${phase}" != "Running" && "${phase}" != "Succeeded" ]]; then
        log "Namespace ${namespace}: pod ${pod} (${app}) en estado ${phase}."
        pending=1
      fi
    done
  done

  return ${pending}
}

wait_for_pods() {
  local deadline=$((SECONDS + POD_TIMEOUT))
  log "Esperando a que Prometheus y Grafana estén en ejecución en cada namespace que empieza por \"${NAMESPACE_PREFIX}\"..."

  while (( SECONDS < deadline )); do
    mapfile -t target_namespaces < <(kubectl get namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null \
      | grep -E "^${NAMESPACE_PREFIX}" || true)

    if (( ${#target_namespaces[@]} == 0 )); then
      log "No se han encontrado namespaces que comiencen por \"${NAMESPACE_PREFIX}\". Reintentando..."
      sleep "${POD_CHECK_INTERVAL}"
      continue
    fi

    local all_ready=1
    for ns in "${target_namespaces[@]}"; do
      if ! pods_ready_in_namespace "${ns}"; then
        all_ready=0
      fi
    done

    if (( all_ready == 1 )); then
      LAST_NAMESPACE_COUNT=${#target_namespaces[@]}
      log "Grafana y Prometheus están en ejecución en todos los namespaces objetivo."
      return 0
    fi

    sleep "${POD_CHECK_INTERVAL}"
  done

  log "Tiempo de espera agotado esperando a los pods de ${APP_NAME}."
  return 1
}

cd "${REPO_DIR}" >/dev/null 2>&1

script_start=$(date +%s)

run_with_timer "make run" make run
run_with_timer "make sincro" make sincro

log "Verificando despliegue de la aplicación ${APP_NAME}..."
wait_for_pods

total_duration=$(( $(date +%s) - script_start ))
log "Tiempo total desde el inicio del script hasta que Prometheus y Grafana están listos: ${total_duration} segundos."

append_log_entry() {
  local timestamp process_type namespace_count duration
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  process_type="application"
  namespace_count=$1
  duration=$2

  mkdir -p "$(dirname "${LOG_FILE}")"
  if [[ ! -f "${LOG_FILE}" ]]; then
    echo "timestamp,tipo,namespaces,duracion_segundos" > "${LOG_FILE}"
  fi

  echo "${timestamp},${process_type},${namespace_count},${duration}" >> "${LOG_FILE}"
}

append_log_entry "${LAST_NAMESPACE_COUNT}" "${total_duration}"
