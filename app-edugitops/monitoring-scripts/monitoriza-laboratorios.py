#!/usr/bin/env python3
"""
Borra reglas HTTPv2 en Checkmk y crea nuevas basadas en alumnos.yaml.
Ahora capaz de leer configuración de src/config.py.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# --- BLOQUE NUEVO: Importar config.py de la carpeta hermana src ---
try:
    # Calculamos la ruta a 'src' basándonos en la ubicación de este script
    script_path = Path(__file__).resolve()
    src_path = script_path.parent.parent / "src"
    
    # Añadimos 'src' al path de Python para poder importar 'config'
    if str(src_path) not in sys.path:
        sys.path.append(str(src_path))
    
    import config # type: ignore
    print("DEBUG: src/config.py importado correctamente en el script.")
except ImportError as e:
    config = None
    print(f"DEBUG: No se pudo importar config.py: {e}")
# ------------------------------------------------------------------


def run_command(command: List[str], cwd: Path | None = None, env: Optional[dict] = None) -> None:
    """Execute a command, exiting with the same code on failure (set -e behavior)."""
    try:
        subprocess.run(
            command,
            check=True,
            cwd=str(cwd) if cwd else None,
            env=env,
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


def load_env_file(path: Path) -> dict:
    """Load a simple KEY=VALUE .env file into a dict."""
    if not path.exists():
        return {}
    env_data: dict = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_data[key.strip()] = value.strip()
    return env_data


def load_rules(alumnos_path: Path) -> List[Tuple[str, str]]:
    """Parse alumnos.yaml and produce a list of (url, service_name) tuples."""
    try:
        import yaml  # type: ignore
    except ImportError:
        print("Se requiere el módulo PyYAML (python3 -m pip install pyyaml).", file=sys.stderr)
        sys.exit(1)

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

    results: List[Tuple[str, str]] = []

    for alumno in data:
        if not isinstance(alumno, dict):
            continue
        nombre = alumno.get("nombre")
        apps = alumno.get("apps") or []
        urls = alumno.get("check-http") or []

        if not nombre:
            continue

        for app, url in zip(apps, urls):
            if not url or not app:
                continue
            service = f"{nombre}-{app}"
            results.append((url, service))

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Borra reglas HTTPv2 y crea nuevas en Checkmk basadas en alumnos.yaml."
    )
    parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    checkmk_dir = script_dir
    
    # Rutas relativas
    alumnos_file = script_dir.parent / "src" / "alumnos.yaml"
    if not alumnos_file.exists():
         alumnos_file = script_dir.parent / "alumnos.yaml"
    
    dotenv_path = script_dir.parent / ".env"
    
    # --- CONSTRUCCIÓN DE VARIABLES DE ENTORNO ---
    # Prioridad: 1. Entorno Real (OS) > 2. Fichero .env > 3. config.py (Fallback)
    
    # 1. Empezamos con el entorno del sistema
    base_env = os.environ.copy()
    
    # 2. Cargamos variables de config.py (si existe) para rellenar huecos
    if config:
        vars_to_sync = [
            "CHECKMK_HOST_NAME", 
            "CHECKMK_HOST_IP",    
            "CHECKMK_API_USER", 
            "CHECKMK_API_SECRET", 
            "CHECKMK_SITE", 
            "CHECKMK_URL"
        ]
        for var in vars_to_sync:
            # Si no está en el entorno pero sí en config, la añadimos
            if var not in base_env and hasattr(config, var):
                val = getattr(config, var)
                if val: # Solo si tiene valor
                    base_env[var] = str(val)

    # 3. Cargamos .env (esto sobrescribe config.py si hay colisión, lo cual es correcto)
    file_env_vars = load_env_file(dotenv_path)
    base_env.update(file_env_vars)

    # validación final
    target_host_name = base_env.get("CHECKMK_HOST_NAME")
    if not target_host_name:
        print("ERROR: Debes definir CHECKMK_HOST_NAME en el entorno, .env o config.py", file=sys.stderr)
        return 1
    # ---------------------------------------------

    print("Limpiando configuración previa en Checkmk...")
    run_command([str(checkmk_dir / "checkmk-borrar-reglas-http2.sh")], env=base_env)

    run_command([str(checkmk_dir / "checkmk-borrar-host.sh")], env=base_env)

    run_command([str(checkmk_dir / "checkmk-crear-host.sh")], env=base_env)

    rules = load_rules(alumnos_file)
    total_rules = len(rules)

    if total_rules == 0:
        print("Sin reglas nuevas en alumnos.yaml. Finalizado.")
        return 0

    print(f"Creando {total_rules} reglas HTTPv2...")
    env_skip_activate = base_env.copy()
    env_skip_activate["SKIP_ACTIVATE"] = "1"

    for url, service_name in rules:
        run_command(
            [
                str(checkmk_dir / "checkmk-crear-regla-http2.sh"),
                target_host_name,
                url,
                service_name,
            ],
            env=env_skip_activate,
        )

    print("Activando cambios pendientes...")
    run_command([str(checkmk_dir / "checkmk-activar-cambios.sh")], env=base_env)

    print("Checkmk actualizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())