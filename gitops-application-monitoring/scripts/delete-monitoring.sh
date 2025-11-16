#!/bin/bash

# This script deletes all generated monitoring-related YAML files for each student.
set -e
echo "Deleting monitoring YAML files for students..."
# echo "Sure you want to proceed? This action cannot be undone. (y/n)"
# read -r confirmation
# if [[ "$confirmation" != "y" ]]; then
#   echo "Deletion cancelled."
#   exit 0
# fi

# Delete namespaces
rm -f alumnos/namespaces/alumno-*.yaml
# Delete networkpolicies
rm -f alumnos/networkpolicies/alumno-*.yaml
# Delete Prometheus - ConfigMaps
rm -f alumnos/prometheus/configmaps/alumno-*.yaml
# Delete Prometheus - PVCs
rm -f alumnos/prometheus/pvcs/alumno-*.yaml
# Delete Prometheus - Deployments
rm -f alumnos/prometheus/deployments/alumno-*.yaml
# Delete Prometheus - Services
rm -f alumnos/prometheus/services/alumno-*.yaml
# Delete Grafana - ConfigMaps
rm -f alumnos/grafana/configmaps/alumno-*.yaml
# Delete Grafana - PVCs
rm -f alumnos/grafana/pvcs/alumno-*.yaml
# Delete Grafana - Secrets
rm -f alumnos/grafana/secrets/alumno-*.yaml
# Delete Grafana - Deployments
rm -f alumnos/grafana/deployments/alumno-*.yaml
# Delete Grafana - Services
rm -f alumnos/grafana/services/alumno-*.yaml
echo "All monitoring YAML files deleted successfully."
exit 0
