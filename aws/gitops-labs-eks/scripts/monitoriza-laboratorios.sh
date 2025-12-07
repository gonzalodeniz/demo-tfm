#!/bin/bash
# Borra todas las reglas HTTPv2 y crea nuevas basadas en alumnos.yaml.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECKMK_DIR="$SCRIPT_DIR"
ALUMNOS_FILE="$SCRIPT_DIR/../alumnos.yaml"
TARGET_HOST_NAME="${TARGET_HOST_NAME:-${CHECKMK_TARGET_HOST:-minikube}}"

echo "--- [Paso 1] Borrando reglas existentes ---"
"$CHECKMK_DIR/checkmk-borrar-reglas-http2.sh"

echo "--- [Paso 2] Generando reglas desde alumnos.yaml ---"
RULE_OUTPUT=$(python3 - "$ALUMNOS_FILE" <<'PY'
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Se requiere el módulo PyYAML (python3 -m pip install pyyaml).", file=sys.stderr)
    sys.exit(1)

alumnos_path = Path(sys.argv[1])
if not alumnos_path.exists():
    print(f"No se encontró el fichero {alumnos_path}", file=sys.stderr)
    sys.exit(1)

try:
    data = yaml.safe_load(alumnos_path.read_text()) or []
except Exception as exc:
    print(f"Error leyendo {alumnos_path}: {exc}", file=sys.stderr)
    sys.exit(1)

if not isinstance(data, list):
    print("El contenido de alumnos.yaml debe ser una lista.", file=sys.stderr)
    sys.exit(1)

for alumno in data:
    if not isinstance(alumno, dict):
        continue
    nombre = alumno.get("nombre")
    apps = alumno.get("apps") or []
    urls = alumno.get("check-http") or []

    if not nombre:
        print("Entrada sin 'nombre' detectada; se omite.", file=sys.stderr)
        continue

    if len(apps) != len(urls):
        print(f"Cantidad de apps ({len(apps)}) y check-http ({len(urls)}) no coincide para {nombre}. Ajusta alumnos.yaml.", file=sys.stderr)
        sys.exit(1)

    for app, url in zip(apps, urls):
        if not url:
            print(f"URL vacía para {nombre}/{app}; se omite.", file=sys.stderr)
            continue
        if not app:
            print(f"App vacía para {nombre} (URL: {url}); se omite.", file=sys.stderr)
            continue
        service = f"{nombre}-{app}"
        print(f"{url}\t{service}")
PY
)
PY_STATUS=$?
if [[ $PY_STATUS -ne 0 ]]; then
  exit $PY_STATUS
fi

mapfile -t RULE_DEFS <<<"$RULE_OUTPUT"

if [[ ${#RULE_DEFS[@]} -eq 0 ]]; then
  echo "No se generaron reglas nuevas desde alumnos.yaml. Finalizado."
  exit 0
fi

echo "--- [Paso 3] Creando reglas nuevas ---"
for entry in "${RULE_DEFS[@]}"; do
  TARGET_URL="${entry%%$'\t'*}"
  SERVICE_NAME="${entry#*$'\t'}"

  echo "Creando regla: $SERVICE_NAME -> $TARGET_URL"
  "$CHECKMK_DIR/checkmk-crear-regla-http2.sh" "$TARGET_HOST_NAME" "$TARGET_URL" "$SERVICE_NAME"
done

echo "Proceso completado."
