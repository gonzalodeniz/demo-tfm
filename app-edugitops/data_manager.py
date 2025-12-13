from __future__ import annotations

import os
from typing import Any, cast

import yaml

# Definimos rutas absolutas
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
ALUMNOS_FILE: str = os.path.join(BASE_DIR, "alumnos.yaml")
CATALOGO_FILE: str = os.path.join(BASE_DIR, "catalogo-servicios.yaml")

YamlItem = dict[str, Any]
YamlData = list[YamlItem]


def _load_yaml(filepath: str) -> YamlData:
    """Función interna para cargar YAML genérico."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            loaded: Any = yaml.safe_load(f)
    except Exception as exc:
        print(f"Error cargando {filepath}: {exc}")
        return []

    if loaded is None or not isinstance(loaded, list):
        return []

    items: YamlData = []
    for item in loaded:
        if isinstance(item, dict):
            items.append(cast(YamlItem, item))
    return items


def load_alumnos() -> YamlData:
    """Devuelve la lista de alumnos."""
    return _load_yaml(ALUMNOS_FILE)


def load_catalogo() -> YamlData:
    """Devuelve la lista de servicios del catálogo."""
    return _load_yaml(CATALOGO_FILE)


def save_alumno_changes(
    student_id: str | int, new_name: str, new_apps: list[str]
) -> tuple[bool, str]:
    """
    Actualiza un alumno, regenera sus URLs check-http y guarda en disco.
    Retorna (True, mensaje) si tiene éxito, o (False, error).
    """
    if not os.path.exists(ALUMNOS_FILE):
        return False, "Archivo de alumnos no encontrado."

    try:
        # 1. Cargar datos
        alumnos_data: YamlData = load_alumnos()
        servicios_data: YamlData = load_catalogo()
        
        # Mapa de puertos para búsqueda rápida: {'grafana': 3000, ...}
        service_ports: dict[str, int] = {}
        for service in servicios_data:
            service_id = service.get("id")
            port = service.get("port")
            if isinstance(service_id, str) and isinstance(port, int):
                service_ports[service_id] = port

        # 2. Buscar y actualizar
        student_found = False
        for alumno in alumnos_data:
            if str(alumno.get('id')) == str(student_id):
                alumno['nombre'] = new_name
                alumno['apps'] = new_apps
                
                # Lógica de negocio: Regenerar URLs check-http
                new_check_http: list[str] = []
                for app_id in new_apps:
                    port = service_ports.get(app_id)
                    if port is not None:
                        url = f"http://{app_id}-service.{new_name}.svc.cluster.local:{port}"
                        new_check_http.append(url)
                
                alumno['check-http'] = new_check_http
                student_found = True
                break
        
        if not student_found:
            return False, "Alumno no encontrado."

        # 3. Guardar en disco
        with open(ALUMNOS_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(alumnos_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return True, "Cambios guardados localmente correctamente."

    except Exception as exc:
        print(f"Error al guardar: {exc}")
        return False, f"Error interno: {str(exc)}"
