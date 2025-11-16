#!/bin/bash
set -euo pipefail

echo "Generating monitoring YAML files for students..."

input_file="${1:-alumnos.txt}"
NAMESPACE_PREFIX="${NAMESPACE_PREFIX:-monitoring}"

slugify() {
  local value
  value=$(echo "$1" | tr '[:upper:]' '[:lower:]')
  value=$(echo "$value" | sed -E 's/[^a-z0-9]+/-/g')
  value=${value#-}
  value=${value%-}
  printf '%s' "${value}"
}

render_template() {
  local template=$1
  local destination=$2
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      -e "s/{{namespace}}/${namespace}/g" \
      "${template}" > "${destination}"
}

# Lee todas las líneas, ignora comentarios y vacías
# Formato esperado: alumno,id_alumno
while IFS=',' read -r alumno id_alumno; do
  # Quita \r por si el CSV viene en CRLF
  alumno=${alumno%$'\r'}
  id_alumno=${id_alumno%$'\r'}

  # Ignora comentarios y líneas vacías
  [[ -z "${alumno}" ]] && continue
  [[ "${alumno:0:1}" == "#" ]] && continue

  alumno_slug=$(slugify "${alumno}")
  id_slug=$(slugify "${id_alumno}")
  namespace="${NAMESPACE_PREFIX}-${alumno_slug}-${id_slug}"

  echo "Using namespace ${namespace} for ${alumno} (${id_alumno})."

  mkdir -p alumnos/namespaces
  echo "Generating namespace YAML for ${namespace}..."
  render_template templates/namespace-template.yaml "alumnos/namespaces/namespace-${namespace}.yaml"

  mkdir -p alumnos/networkpolicies
  echo "Generating networkpolicy YAML for ${namespace}..."
  render_template templates/networkpolicies-template.yaml "alumnos/networkpolicies/networkpolicy-${namespace}.yaml"

  mkdir -p alumnos/prometheus/configmaps
  echo "Generating Prometheus ConfigMap YAML for ${namespace}..."
  render_template templates/prometheus/configmap-template.yaml "alumnos/prometheus/configmaps/prometheus-config-${namespace}.yaml"

  mkdir -p alumnos/prometheus/pvcs
  echo "Generating Prometheus PVC YAML for ${namespace}..."
  render_template templates/prometheus/pvc-template.yaml "alumnos/prometheus/pvcs/prometheus-pvc-${namespace}.yaml"

  mkdir -p alumnos/prometheus/deployments
  echo "Generating Prometheus Deployment YAML for ${namespace}..."
  render_template templates/prometheus/deployment-template.yaml "alumnos/prometheus/deployments/prometheus-deploy-${namespace}.yaml"

  mkdir -p alumnos/prometheus/services
  echo "Generating Prometheus Service YAML for ${namespace}..."
  render_template templates/prometheus/service-template.yaml "alumnos/prometheus/services/prometheus-service-${namespace}.yaml"

  mkdir -p alumnos/grafana/configmaps
  echo "Generating Grafana ConfigMap YAML for ${namespace}..."
  render_template templates/grafana/configmap-template.yaml "alumnos/grafana/configmaps/grafana-config-${namespace}.yaml"

  mkdir -p alumnos/grafana/pvcs
  echo "Generating Grafana PVC YAML for ${namespace}..."
  render_template templates/grafana/pvc-template.yaml "alumnos/grafana/pvcs/grafana-pvc-${namespace}.yaml"

  mkdir -p alumnos/grafana/secrets
  echo "Generating Grafana Secret YAML for ${namespace}..."
  render_template templates/grafana/secret-template.yaml "alumnos/grafana/secrets/grafana-secret-${namespace}.yaml"

  mkdir -p alumnos/grafana/deployments
  echo "Generating Grafana Deployment YAML for ${namespace}..."
  render_template templates/grafana/deployment-template.yaml "alumnos/grafana/deployments/grafana-deploy-${namespace}.yaml"

  mkdir -p alumnos/grafana/services
  echo "Generating Grafana Service YAML for ${namespace}..."
  render_template templates/grafana/service-template.yaml "alumnos/grafana/services/grafana-service-${namespace}.yaml"

done < <(grep -v '^[[:space:]]*$' "$input_file" | grep -v '^[[:space:]]*#')

echo "All monitoring YAML files generated successfully."
