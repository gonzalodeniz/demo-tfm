#!/bin/bash
# Generate namespace YAML files for each student listed in alumnos.txt (CSV format)
# using namespace-template.yaml as a template.

# Create output directory if it doesn't exist
mkdir -p namespaces

# Read CSV file, skipping the header line
tail -n +2 alumnos.txt | while IFS=',' read -r alumno id_alumno; do
  # Skip empty lines
  [ -z "$alumno" ] && continue
  
  # Replace {{alumno}} and {{id_alumno}} in the template with actual values
  sed -e "s/{{alumno}}/${alumno}/g" \
      -e "s/{{id_alumno}}/${id_alumno}/g" \
      templates/namespace-template.yaml \
    > "namespaces/alumno-${alumno}-${id_alumno}.yaml"
done
