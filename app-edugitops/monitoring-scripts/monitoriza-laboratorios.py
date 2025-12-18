#!/usr/bin/env python3
"""
Orquestador de Monitorización para Checkmk.
Soporta reglas HTTP y TCP basándose en catalogo-servicios.yaml.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import yaml # type: ignore
from pathlib import Path
from typing import List, Dict, Any

# --- Importar config.py ---
try:
    script_path = Path(__file__).resolve()
    src_path = script_path.parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.append(str(src_path))
    import config # type: ignore
except ImportError:
    config = None

def run_command(command: List[str], env: Dict[str, str]) -> None:
    """Ejecuta comando bash y sale si falla."""
    try:
        subprocess.run(command, check=True, env=env)
    except subprocess.CalledProcessError as exc:
        print(f"❌ Error ejecutando {command[0]}: {exc}")
        sys.exit(exc.returncode)

def load_catalog(catalog_path: Path) -> Dict[str, Dict[str, Any]]:
    """Carga el catálogo y devuelve un mapa {app_id: {protocol, port, ...}}."""
    if not catalog_path.exists():
        print(f"⚠️ No se encuentra el catálogo en {catalog_path}")
        return {}
    
    try:
        data = yaml.safe_load(catalog_path.read_text()) or []
        catalog = {}
        for item in data:
            if 'id' in item:
                catalog[item['id']] = item
        return catalog
    except Exception as e:
        print(f"❌ Error leyendo catálogo: {e}")
        sys.exit(1)

def load_students(alumnos_path: Path) -> List[Dict[str, Any]]:
    """Carga lista de alumnos."""
    if not alumnos_path.exists():
        return []
    try:
        return yaml.safe_load(alumnos_path.read_text()) or []
    except Exception:
        return []

def main() -> int:
    parser = argparse.ArgumentParser(description="Configura monitorización HTTP/TCP en Checkmk.")
    parser.parse_args()

    # 1. Definir rutas
    script_dir = Path(__file__).resolve().parent
    root_dir = script_dir.parent
    
    # Buscamos ficheros en src/ (estructura Docker) o relativo (estructura local)
    alumnos_file = root_dir / "src" / "alumnos.yaml"
    if not alumnos_file.exists(): alumnos_file = root_dir / "alumnos.yaml"
    
    catalog_file = root_dir / "src" / "catalogo-servicios.yaml"
    if not catalog_file.exists(): catalog_file = root_dir / "catalogo-servicios.yaml"

    # 2. Preparar entorno
    base_env = os.environ.copy()
    if config:
        vars_to_sync = ["CHECKMK_HOST_NAME", "CHECKMK_HOST_IP", "CHECKMK_API_USER", 
                        "CHECKMK_API_SECRET", "CHECKMK_SITE", "CHECKMK_URL"]
        for var in vars_to_sync:
            if var not in base_env and hasattr(config, var):
                val = getattr(config, var)
                if val: base_env[var] = str(val)

    # Validar Hostname
    target_host_name = base_env.get("CHECKMK_HOST_NAME")
    if not target_host_name:
        print("❌ ERROR: CHECKMK_HOST_NAME no definido.")
        return 1

    # 3. Limpieza Inicial
    print("🧹 [1/4] Limpiando reglas antiguas (HTTP y TCP)...")
    run_command([str(script_dir / "checkmk-borrar-reglas-http2.sh")], env=base_env)
    run_command([str(script_dir / "checkmk-borrar-reglas-tcp.sh")], env=base_env)
    
    # Reiniciar host (opcional, para asegurar limpieza)
    run_command([str(script_dir / "checkmk-borrar-host.sh")], env=base_env)
    run_command([str(script_dir / "checkmk-crear-host.sh")], env=base_env)

    # 4. Cargar Datos
    catalog = load_catalog(catalog_file)
    students = load_students(alumnos_file)

    if not students:
        print("ℹ️ No hay alumnos. Finalizando.")
        return 0

    print(f"⚙️ [2/4] Procesando {len(students)} alumnos...")
    
    # Entorno para creación masiva (sin activar cambios cada vez)
    env_batch = base_env.copy()
    env_batch["SKIP_ACTIVATE"] = "1"

    count_http = 0
    count_tcp = 0

    for alumno in students:
        nombre = alumno.get("nombre", "").strip()
        apps = alumno.get("apps", [])
        
        if not nombre: continue

        for app_id in apps:
            if app_id not in catalog:
                print(f"⚠️ App desconocida '{app_id}' para {nombre}. Saltando.")
                continue
            
            app_info = catalog[app_id]
            protocol = app_info.get("protocol", "http").lower()
            port = app_info.get("port")
            
            # Construir nombre de servicio K8s: <app>-service.<alumno>.svc.cluster.local
            # Nota: Esto asume tu convención de nombres estándar
            k8s_dns = f"{app_id}-service.{nombre}.svc.cluster.local"
            service_label = f"{nombre}-{app_id}"

            if protocol == "http":
                # Construir URL completa
                target_url = f"http://{k8s_dns}:{port}"
                print(f"   Creating HTTP: {service_label} -> {target_url}")
                run_command([
                    str(script_dir / "checkmk-crear-regla-http2.sh"),
                    target_host_name,
                    target_url,
                    service_label
                ], env=env_batch)
                count_http += 1
                
            elif protocol == "tcp":
                print(f"   Creating TCP: {service_label} -> {k8s_dns}:{port}")
                run_command([
                    str(script_dir / "checkmk-crear-regla-tcp.sh"),
                    target_host_name,
                    k8s_dns,
                    str(port),
                    service_label
                ], env=env_batch)
                count_tcp += 1

    print(f"📊 Resumen: {count_http} reglas HTTP, {count_tcp} reglas TCP creadas.")

    # 5. Activar Cambios
    print("🚀 [3/4] Activando cambios en Checkmk...")
    run_command([str(script_dir / "checkmk-activar-cambios.sh")], env=base_env)

    print("✅ [4/4] Proceso completado con éxito.")
    return 0

if __name__ == "__main__":
    sys.exit(main())