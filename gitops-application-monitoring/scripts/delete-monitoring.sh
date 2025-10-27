#!/bin/bash

# This script deletes all generated monitoring-related YAML files for each student.
set -e
echo "Deleting monitoring YAML files for students..."
echo "Sure you want to proceed? This action cannot be undone. (y/n)"
read -r confirmation
if [[ "$confirmation" != "y" ]]; then
  echo "Deletion cancelled."
  exit 0
fi

# Delete namespaces
rm -f namespaces/alumno-*.yaml
# Delete networkpolicies
rm -f networkpolicies/alumno-*.yaml
# Delete Prometheus - ConfigMaps
rm -f prometheus/configmaps/alumno-*.yaml
# Delete Prometheus - PVCs
rm -f prometheus/pvcs/alumno-*.yaml
# Delete Prometheus - Deployments
rm -f prometheus/deployments/alumno-*.yaml
# Delete Prometheus - Services
rm -f prometheus/services/alumno-*.yaml
# Delete Grafana - ConfigMaps
rm -f grafana/configmaps/alumno-*.yaml
# Delete Grafana - PVCs
rm -f grafana/pvcs/alumno-*.yaml
# Delete Grafana - Secrets
rm -f grafana/secrets/alumno-*.yaml
# Delete Grafana - Deployments
rm -f grafana/deployments/alumno-*.yaml
echo "All monitoring YAML files deleted successfully."
exit 0
