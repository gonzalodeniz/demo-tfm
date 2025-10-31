#!/bin/bash
set -euo pipefail

echo "Generating monitoring YAML files for students..."

input_file="${1:-alumnos.txt}"

# Lee todas las líneas, ignora comentarios y vacías
# Formato esperado: alumno,id_alumno
while IFS=',' read -r alumno id_alumno; do
  # Quita \r por si el CSV viene en CRLF
  alumno=${alumno%$'\r'}
  id_alumno=${id_alumno%$'\r'}

  # Ignora comentarios y líneas vacías
  [[ -z "${alumno}" ]] && continue
  [[ "${alumno:0:1}" == "#" ]] && continue

  echo "Generating namespace YAML for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/namespaces
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/namespace-template.yaml > "alumnos/namespaces/alumno-${alumno}-${id_alumno}.yaml"

  echo "Generating networkpolicy YAML for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/networkpolicies
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/networkpolicies-template.yaml > "alumnos/networkpolicies/alumno-${alumno}-${id_alumno}.yaml"

  echo "Generating Prometheus-ConfigMap YAML files for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/prometheus/configmaps
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/prometheus/configmap-template.yaml > "alumnos/prometheus/configmaps/alumno-${alumno}-${id_alumno}.yaml"

  echo "Generating Prometheus-PVC YAML files for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/prometheus/pvcs
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/prometheus/pvc-template.yaml > "alumnos/prometheus/pvcs/alumno-${alumno}-${id_alumno}.yaml"

  echo "Generating Prometheus-Deployment YAML files for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/prometheus/deployments
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/prometheus/deployment-template.yaml > "alumnos/prometheus/deployments/alumno-${alumno}-${id_alumno}.yaml"

  echo "Generating Prometheus-Service YAML files for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/prometheus/services
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/prometheus/service-template.yaml > "alumnos/prometheus/services/alumno-${alumno}-${id_alumno}.yaml"

  echo "Generating Grafana-ConfigMap YAML files for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/grafana/configmaps
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/grafana/configmap-template.yaml > "alumnos/grafana/configmaps/alumno-${alumno}-${id_alumno}.yaml"

  echo "Generating Grafana-PVC YAML files for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/grafana/pvcs
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/grafana/pvc-template.yaml > "alumnos/grafana/pvcs/alumno-${alumno}-${id_alumno}.yaml"

  echo "Generating Grafana-Secret YAML files for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/grafana/secrets
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/grafana/secret-template.yaml > "alumnos/grafana/secrets/alumno-${alumno}-${id_alumno}.yaml"

  echo "Generating Grafana-Deployment YAML files for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/grafana/deployments
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/grafana/deployment-template.yaml > "alumnos/grafana/deployments/alumno-${alumno}-${id_alumno}.yaml"

  echo "Generating Grafana-Service YAML files for ${alumno} (${id_alumno})..."
  mkdir -p alumnos/grafana/services
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/grafana/service-template.yaml > "alumnos/grafana/services/alumno-${alumno}-${id_alumno}.yaml"

done < <(grep -v '^[[:space:]]*$' "$input_file" | grep -v '^[[:space:]]*#')

echo "All monitoring YAML files generated successfully."
