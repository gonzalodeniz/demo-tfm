#!/usr/bin/env python3
"""
Borra reglas HTTPv2 en Checkmk y crea nuevas basadas en alumnos.yaml.
Replica el comportamiento del script Bash monitoriza-laboratorios.sh.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional


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
    """
    Parse alumnos.yaml and produce a list of (url, service_name) tuples.
    Mimics the inline Python logic from the original Bash script.
    """
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
            print("Entrada sin 'nombre' detectada; se omite.", file=sys.stderr)
            continue

        if len(apps) != len(urls):
            print(
                f"Cantidad de apps ({len(apps)}) y check-http ({len(urls)}) no coincide para {nombre}. Ajusta alumnos.yaml.",
                file=sys.stderr,
            )
            sys.exit(1)

        for app, url in zip(apps, urls):
            if not url:
                print(f"URL vacía para {nombre}/{app}; se omite.", file=sys.stderr)
                continue
            if not app:
                print(f"App vacía para {nombre} (URL: {url}); se omite.", file=sys.stderr)
                continue
            service = f"{nombre}-{app}"
            results.append((url, service))

    return results


def main() -> int:
    """Entry point replicating monitoriza-laboratorios.sh behavior."""
    parser = argparse.ArgumentParser(
        description="Borra reglas HTTPv2 y crea nuevas en Checkmk basadas en alumnos.yaml."
    )
    parser.parse_args()  # No arguments, but kept for parity and future extensibility.

    script_dir = Path(__file__).resolve().parent
    checkmk_dir = script_dir
    alumnos_file = script_dir.parent / "alumnos.yaml"
    dotenv_path = script_dir.parent / ".env"
    base_env = os.environ.copy()
    base_env.update(load_env_file(dotenv_path))
    target_host_name = (
        base_env.get("CHECKMK_HOST_NAME")
        or base_env.get("CHECKMK_TARGET_HOST")
        or "minikube"
    )

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
