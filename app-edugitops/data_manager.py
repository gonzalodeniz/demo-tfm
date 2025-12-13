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

# ... (Mantén las funciones _load_yaml, load_alumnos, load_catalogo existentes) ...
def _load_yaml(filepath: str) -> YamlData:
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
    return _load_yaml(ALUMNOS_FILE)

def load_catalogo() -> YamlData:
    return _load_yaml(CATALOGO_FILE)

# ... (Mantén get_next_student_id, save_alumno_changes, delete_student existentes) ...
def get_next_student_id() -> str:
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

def save_alumno_changes(student_id: str | int, new_name: str, new_apps: list[str]) -> tuple[bool, str]:
    # ... (Tu código existente de save_alumno_changes) ...
    # (Omito el cuerpo para ahorrar espacio, ya lo tienes del paso anterior)
    if not os.path.exists(ALUMNOS_FILE) and not isinstance(load_alumnos(), list):
         alumnos_data: YamlData = []
    else:
        alumnos_data = load_alumnos()
    servicios_data: YamlData = load_catalogo()
    for alumno in alumnos_data:
        existing_id = str(alumno.get("id"))
        existing_name = str(alumno.get("nombre", "")).strip().lower()
        if existing_name == new_name.strip().lower() and existing_id != str(student_id):
            return False, f"El nombre '{new_name}' ya está en uso por otro alumno."
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
    student_found = False
    for alumno in alumnos_data:
        if str(alumno.get('id')) == str(student_id):
            alumno['nombre'] = new_name.strip()
            alumno['apps'] = new_apps
            alumno['check-http'] = new_check_http
            student_found = True
            break
    if not student_found:
        new_student: YamlItem = {
            "nombre": new_name.strip(),
            "id": str(student_id),
            "apps": new_apps,
            "check-http": new_check_http
        }
        alumnos_data.append(new_student)
    try:
        with open(ALUMNOS_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(alumnos_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        action_type = "actualizado" if student_found else "creado"
        return True, f"Alumno {action_type} correctamente."
    except Exception as exc:
        print(f"Error al guardar: {exc}")
        return False, f"Error interno: {str(exc)}"

def delete_student(student_id: str | int) -> tuple[bool, str]:
    # ... (Tu código existente de delete_student) ...
    if not os.path.exists(ALUMNOS_FILE):
        return False, "Fichero de alumnos no encontrado."
    alumnos = load_alumnos()
    initial_count = len(alumnos)
    new_alumnos = [a for a in alumnos if str(a.get('id')) != str(student_id)]
    if len(new_alumnos) == initial_count:
        return False, "Alumno no encontrado."
    try:
        with open(ALUMNOS_FILE, "w", encoding="utf-8") as f:
             yaml.safe_dump(new_alumnos, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return True, "Alumno eliminado correctamente."
    except Exception as exc:
        return False, f"Error al borrar: {str(exc)}"

# --- NUEVAS FUNCIONES PARA EL EDITOR RAW ---

def get_raw_alumnos_yaml() -> str:
    """Lee el archivo alumnos.yaml tal cual, como texto."""
    if not os.path.exists(ALUMNOS_FILE):
        return ""
    try:
        with open(ALUMNOS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def validate_and_save_raw_yaml(raw_text: str) -> tuple[bool, str]:
    """
    Parsea, valida reglas de negocio complejas y guarda el YAML raw.
    """
    # 1. Validación de Sintaxis YAML
    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as e:
        return False, f"Error de sintaxis YAML: {str(e)}"

    if data is None: 
        # Archivo vacío es válido (borrar todos), pero aseguramos que sea lista
        data = []
    
    if not isinstance(data, list):
        return False, "El YAML debe ser una lista de alumnos (comenzar con guiones '-')."

    # 2. Cargar catálogo para validaciones
    servicios = load_catalogo()
    # Mapa { 'grafana': 3000 }
    valid_apps_ports: dict[str, int] = {}
    for s in servicios:
        if isinstance(s.get('id'), str) and isinstance(s.get('port'), int):
            valid_apps_ports[s['id']] = s['port']

    seen_ids = set()
    seen_names = set()

    # 3. Validaciones de Negocio por Alumno
    for idx, alumno in enumerate(data):
        if not isinstance(alumno, dict):
            return False, f"El elemento #{idx+1} no es un objeto válido."

        # A. Validar ID (Existencia y Duplicados)
        sid = str(alumno.get('id', '')).strip()
        if not sid:
            return False, f"El alumno #{idx+1} no tiene ID."
        if sid in seen_ids:
            return False, f"ID duplicado encontrado: {sid}"
        seen_ids.add(sid)

        # B. Validar Nombre (Existencia y Duplicados)
        nombre = str(alumno.get('nombre', '')).strip()
        if not nombre:
            return False, f"El alumno con ID {sid} no tiene nombre."
        if nombre.lower() in seen_names:
            return False, f"Nombre duplicado encontrado: {nombre}"
        seen_names.add(nombre.lower())

        # C. Validar Apps (Deben existir en catálogo)
        apps = alumno.get('apps', [])
        if not isinstance(apps, list):
            return False, f"La lista 'apps' del alumno {nombre} es inválida."
        
        for app in apps:
            if app not in valid_apps_ports:
                return False, f"La aplicación '{app}' asignada a {nombre} no existe en el catálogo."

        # D. Validar Check-HTTP (Formato Estricto)
        # Generamos las URLs esperadas según las apps que tiene asignadas
        expected_urls = set()
        for app in apps:
            port = valid_apps_ports[app]
            url = f"http://{app}-service.{nombre}.svc.cluster.local:{port}"
            expected_urls.add(url)
        
        current_urls = set(alumno.get('check-http', []))
        
        # Comparamos conjuntos: las URLs presentes deben coincidir exactamente con las esperadas
        if current_urls != expected_urls:
            return False, f"Error en 'check-http' para {nombre}. Las URLs no coinciden con las apps asignadas o el formato es incorrecto."

    # 4. Si pasa todo, guardamos
    try:
        # Usamos safe_dump sobre la DATA parseada para asegurar formato limpio, 
        # o escribimos el raw_text si confiamos en el usuario. 
        # Para garantizar formato consistente, mejor volcamos 'data'.
        with open(ALUMNOS_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return True, "Fichero YAML validado y guardado correctamente."
    except Exception as e:
        return False, f"Error de escritura: {str(e)}"