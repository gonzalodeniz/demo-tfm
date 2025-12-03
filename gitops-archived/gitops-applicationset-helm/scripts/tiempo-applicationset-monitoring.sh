#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

NAMESPACE_PREFIX="${NAMESPACE_PREFIX:-monitoring}"
POD_TIMEOUT="${POD_TIMEOUT:-600}"
POD_CHECK_INTERVAL="${POD_CHECK_INTERVAL:-5}"
REQUIRED_APPS=("grafana" "prometheus")
GLOBAL_LOG_FILE="/home/gdeniz/Workspaces/formacion/unir/tfm/demo-tfm/repo/tiempos-ejecuciones.csv"
LOG_FILE="${LOG_FILE:-${GLOBAL_LOG_FILE}}"
ALUMNOS_FILE="${ALUMNOS_FILE:-${REPO_DIR}/alumnos.yaml}"

LAST_NAMESPACE_COUNT=0
EXPECTED_NAMESPACE_COUNT=0
declare -a EXPECTED_NAMESPACES=()

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

namespace_exists() {
  kubectl get namespace "$1" >/dev/null 2>&1
}

load_expected_namespaces() {
  local alumnos_file=$1
  if [[ ! -f "${alumnos_file}" ]]; then
    log "Archivo ${alumnos_file} no encontrado. Se usará detección dinámica de namespaces."
    return
  fi

  if ! mapfile -t EXPECTED_NAMESPACES < <(awk -v prefix="${NAMESPACE_PREFIX}" '
/^- *nombre:/ {
  gsub(/^- *nombre:[ \t]*/, "");
  nombre=$0;
  gsub(/"/, "", nombre);
}
/^[ \t]*id:/ {
  gsub(/^[ \t]*id:[ \t]*/, "");
  identificador=$0;
  gsub(/"/, "", identificador);
  if (nombre != "" && identificador != "") {
    printf "%s-%s-%s\n", prefix, nombre, identificador;
    nombre="";
    identificador="";
  }
}
' "${alumnos_file}"); then
    log "No se pudieron obtener namespaces esperados a partir de ${alumnos_file}. Se usará detección dinámica."
    EXPECTED_NAMESPACES=()
    EXPECTED_NAMESPACE_COUNT=0
    return
  fi

  EXPECTED_NAMESPACE_COUNT=${#EXPECTED_NAMESPACES[@]}
  if (( EXPECTED_NAMESPACE_COUNT == 0 )); then
    log "No se encontraron entradas válidas en ${alumnos_file}. Se usará detección dinámica de namespaces."
  else
    log "Se esperan ${EXPECTED_NAMESPACE_COUNT} namespaces con el prefijo \"${NAMESPACE_PREFIX}\"."
  fi
}

wait_for_pods() {
  local deadline=$((SECONDS + POD_TIMEOUT))
  log "Esperando a que Prometheus y Grafana estén en ejecución en cada namespace que empieza por \"${NAMESPACE_PREFIX}\"..."

  while (( SECONDS < deadline )); do
    local -a target_namespaces=()
    if (( EXPECTED_NAMESPACE_COUNT > 0 )); then
      target_namespaces=("${EXPECTED_NAMESPACES[@]}")
    else
      mapfile -t target_namespaces < <(kubectl get namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' 2>/dev/null \
        | grep -E "^${NAMESPACE_PREFIX}" || true)
    fi

    if (( ${#target_namespaces[@]} == 0 )); then
      log "No se han encontrado namespaces que comiencen por \"${NAMESPACE_PREFIX}\". Reintentando..."
      sleep "${POD_CHECK_INTERVAL}"
      continue
    fi

    local all_ready=1
    for ns in "${target_namespaces[@]}"; do
      if (( EXPECTED_NAMESPACE_COUNT > 0 )) && ! namespace_exists "${ns}"; then
        log "Namespace ${ns} aún no existe."
        all_ready=0
        continue
      fi

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

  log "Tiempo de espera agotado esperando a los pods esperados."
  return 1
}

append_log_entry() {
  local namespace_count duration timestamp process_type
  namespace_count=$1
  duration=$2
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  process_type="aplicationset-helm"

  mkdir -p "$(dirname "${LOG_FILE}")"
  if [[ ! -f "${LOG_FILE}" ]]; then
    echo "timestamp,tipo,namespaces,duracion_segundos" > "${LOG_FILE}"
  fi

  echo "${timestamp},${process_type},${namespace_count},${duration}" >> "${LOG_FILE}"
}

load_expected_namespaces "${ALUMNOS_FILE}"

cd "${REPO_DIR}" >/dev/null 2>&1

sync_start=$(date +%s)
run_with_timer "make sincro" make sincro

log "Verificando despliegue..."
wait_for_pods

total_duration=$(( $(date +%s) - sync_start ))
log "Tiempo total desde el inicio de 'make sincro' hasta que los pods están listos: ${total_duration} segundos."

append_log_entry "${LAST_NAMESPACE_COUNT}" "${total_duration}"
