#!/bin/bash
# Generate a namespace YAML file for each student listed in alumnos.txt
# using namespace-template.yaml as a template.

# Create output directory if it doesn't exist
mkdir -p repo/namespaces

# Read each line from alumnos.txt and create a namespace YAML file
while read alumno; do
  # Skip empty lines
  [ -z "$alumno" ] && continue
  
  # Replace {{alumno}} in the template with the actual student name
  sed "s/{{alumno}}/${alumno}/g" templates/namespace-template.yaml \
    > "namespaces/alumno-${alumno}.yaml"
done < alumnos.txt
