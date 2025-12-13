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


def get_next_student_id() -> str:
    """Calcula el siguiente ID disponible basado en los existentes."""
    alumnos = load_alumnos()
    max_id = 0
    for alumno in alumnos:
        try:
            curr_id = int(str(alumno.get("id", 0)))
            if curr_id > max_id:
                max_id = curr_id
        except (ValueError, TypeError):
            continue
    return str(max_id + 1).zfill(3)


def save_alumno_changes(
    student_id: str | int, new_name: str, new_apps: list[str]
) -> tuple[bool, str]:
    """
    Guarda un alumno. 
    - Si el ID existe: Actualiza.
    - Si el ID no existe: Crea uno nuevo.
    - Valida que el nombre no esté duplicado por otro usuario.
    """
    if not os.path.exists(ALUMNOS_FILE) and not isinstance(load_alumnos(), list):
         # Si no existe, asumimos lista vacía para crear el primero
         alumnos_data: YamlData = []
    else:
        alumnos_data = load_alumnos()
        
    servicios_data: YamlData = load_catalogo()
    
    # 1. Validación de unicidad de nombre
    for alumno in alumnos_data:
        existing_id = str(alumno.get("id"))
        existing_name = str(alumno.get("nombre", "")).strip().lower()
        
        # Si el nombre coincide Y el ID es distinto, es un duplicado prohibido.
        if existing_name == new_name.strip().lower() and existing_id != str(student_id):
            return False, f"El nombre '{new_name}' ya está en uso por otro alumno."

    # 2. Preparar mapa de puertos y URLs
    service_ports: dict[str, int] = {}
    for service in servicios_data:
        sid = service.get("id")
        port = service.get("port")
        if isinstance(sid, str) and isinstance(port, int):
            service_ports[sid] = port

    new_check_http: list[str] = []
    for app_id in new_apps:
        port = service_ports.get(app_id)
        if port is not None:
            url = f"http://{app_id}-service.{new_name.strip()}.svc.cluster.local:{port}"
            new_check_http.append(url)

    # 3. Buscar para Actualizar o Crear
    student_found = False
    for alumno in alumnos_data:
        if str(alumno.get('id')) == str(student_id):
            # ACTUALIZAR
            alumno['nombre'] = new_name.strip()
            alumno['apps'] = new_apps
            alumno['check-http'] = new_check_http
            student_found = True
            break
    
    if not student_found:
        # CREAR NUEVO
        new_student: YamlItem = {
            "nombre": new_name.strip(),
            "id": str(student_id),
            "apps": new_apps,
            "check-http": new_check_http
        }
        alumnos_data.append(new_student)

    # 4. Guardar en disco
    try:
        with open(ALUMNOS_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(alumnos_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        action_type = "actualizado" if student_found else "creado"
        return True, f"Alumno {action_type} correctamente."

    except Exception as exc:
        print(f"Error al guardar: {exc}")
        return False, f"Error interno: {str(exc)}"


def delete_student(student_id: str | int) -> tuple[bool, str]:
    """Elimina un alumno por su ID."""
    if not os.path.exists(ALUMNOS_FILE):
        return False, "Fichero de alumnos no encontrado."
    
    alumnos = load_alumnos()
    initial_count = len(alumnos)
    
    # Filtramos para eliminar el que coincida
    # Usamos str() para asegurar comparación correcta
    new_alumnos = [a for a in alumnos if str(a.get('id')) != str(student_id)]
    
    if len(new_alumnos) == initial_count:
        return False, "Alumno no encontrado."
        
    try:
        with open(ALUMNOS_FILE, "w", encoding="utf-8") as f:
             yaml.safe_dump(new_alumnos, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return True, "Alumno eliminado correctamente."
    except Exception as exc:
        return False, f"Error al borrar: {str(exc)}"