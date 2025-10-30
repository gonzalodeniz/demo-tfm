#!/bin/bash
set -e
# Generate all monitoring-related YAML files for each student listed in alumnos.txt (CSV format)
# using various templates located in the templates/ directory.

echo "Generating monitoring YAML files for students..."

# Read CSV file, skipping the header line
tail -n +2 alumnos.txt | while IFS=',' read -r alumno id_alumno; do
  # Skip empty lines
  [ -z "$alumno" ] && continue
  
    # Namespaces
    echo "Generating namespace YAML for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/namespaces
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/namespace-template.yaml > "alumnos/namespaces/alumno-${alumno}-${id_alumno}.yaml"

    # NetworkPolicies
    echo "Generating networkpolicy YAML for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/networkpolicies
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/networkpolicies-template.yaml > "alumnos/networkpolicies/alumno-${alumno}-${id_alumno}.yaml"

    # Prometheus - ConfigMaps
    echo "Generating Prometheus-ConfigMap YAML files for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/prometheus/configmaps
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/prometheus/configmap-template.yaml  > "alumnos/prometheus/configmaps/alumno-${alumno}-${id_alumno}.yaml"

    # Prometheus - pvc
    echo "Generating Prometheus-PVC YAML files for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/prometheus/pvcs
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/prometheus/pvc-template.yaml  > "alumnos/prometheus/pvcs/alumno-${alumno}-${id_alumno}.yaml"

    # Prometheus - deployments
    echo "Generating Prometheus-Deployment YAML files for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/prometheus/deployments
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/prometheus/deployment-template.yaml  > "alumnos/prometheus/deployments/alumno-${alumno}-${id_alumno}.yaml"

    # Prometheus - services
    echo "Generating Prometheus-Service YAML files for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/prometheus/services
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/prometheus/service-template.yaml  > "alumnos/prometheus/services/alumno-${alumno}-${id_alumno}.yaml"

    # Grafana - configmaps
    echo "Generating Grafana-ConfigMap YAML files for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/grafana/configmaps
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/grafana/configmap-template.yaml  > "alumnos/grafana/configmaps/alumno-${alumno}-${id_alumno}.yaml"

    # Grafana - pvcs
    echo "Generating Grafana-PVC YAML files for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/grafana/pvcs
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/grafana/pvc-template.yaml  > "alumnos/grafana/pvcs/alumno-${alumno}-${id_alumno}.yaml"

    # Grafana - secrets
    echo "Generating Grafana-Secret YAML files for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/grafana/secrets
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/grafana/secret-template.yaml  > "alumnos/grafana/secrets/alumno-${alumno}-${id_alumno}.yaml"

    # Grafana - deployments
    echo "Generating Grafana-Deployment YAML files for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/grafana/deployments
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/grafana/deployment-template.yaml  > "alumnos/grafana/deployments/alumno-${alumno}-${id_alumno}.yaml"

    # Grafana - services
    echo "Generating Grafana-Service YAML files for ${alumno} (${id_alumno})..."
    mkdir -p alumnos/grafana/services
    sed -e "s/{{alumno}}/${alumno}/g" \
        -e "s/{{id_alumno}}/${id_alumno}/g" \
        templates/grafana/service-template.yaml  > "alumnos/grafana/services/alumno-${alumno}-${id_alumno}.yaml"
done
echo "All monitoring YAML files generated successfully."
exit 0