from __future__ import annotations

import os
import base64
import requests
import yaml
from typing import Any, cast

# Importamos la configuración para Gitea
import config

# Definimos rutas absolutas
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
ALUMNOS_FILE: str = os.path.join(BASE_DIR, "alumnos.yaml")
CATALOGO_FILE: str = os.path.join(BASE_DIR, "catalogo-servicios.yaml")

# Variable global para almacenar el estado de la sincro con Gitea
GIT_SYNC_STATUS: bool = False

YamlItem = dict[str, Any]
YamlData = list[YamlItem]


def _load_yaml(filepath: str) -> YamlData:
    """Función interna para cargar YAML genérico de forma segura."""
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
    """Devuelve la lista de alumnos parseada."""
    return _load_yaml(ALUMNOS_FILE)


def load_catalogo() -> YamlData:
    """Devuelve la lista de servicios del catálogo parseada."""
    return _load_yaml(CATALOGO_FILE)


def get_raw_alumnos_yaml() -> str:
    """Lee el archivo alumnos.yaml tal cual, como texto plano."""
    if not os.path.exists(ALUMNOS_FILE):
        return ""
    try:
        with open(ALUMNOS_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def _download_file_from_gitea(remote_path: str, local_path: str) -> bool:
    """Descarga un fichero de Gitea y sobrescribe el local."""
    api_url = f"{config.GITEA_API_URL}/repos/{config.GITEA_REPO_OWNER}/{config.GITEA_REPO_NAME}/contents/{remote_path}"
    auth_creds = (config.GITEA_USER, config.GITEA_PASSWORD)
    params = {'ref': config.GITEA_BRANCH}

    try:
        print(f"DEBUG: Descargando {remote_path} de Gitea...")
        response = requests.get(api_url, auth=auth_creds, params=params, timeout=5)
        
        if response.status_code == 200:
            content_b64 = response.json().get('content', '')
            file_content = base64.b64decode(content_b64).decode('utf-8')
            
            # Sobrescribimos el fichero local
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            print(f"DEBUG: {remote_path} actualizado correctamente.")
            return True
        else:
            print(f"DEBUG: Fallo al descargar {remote_path}. Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"DEBUG: Excepción al descargar {remote_path}: {e}")
        return False

def sync_files_from_gitea() -> bool:
    """
    Intenta descargar alumnos.yaml y catalogo-servicios.yaml.
    Actualiza la variable global GIT_SYNC_STATUS.
    """
    global GIT_SYNC_STATUS
    
    # MODIFICACIÓN: Usamos las rutas REMOTAS (_REMOTE) para pedir a la API,
    # pero guardamos en las rutas locales constantes (ALUMNOS_FILE, CATALOGO_FILE).
    success_alumnos = _download_file_from_gitea(config.GITEA_FILE_PATH_REMOTE, ALUMNOS_FILE)
    success_catalogo = _download_file_from_gitea(config.GITEA_CATALOGO_PATH_REMOTE, CATALOGO_FILE)
    
    if success_alumnos and success_catalogo:
        GIT_SYNC_STATUS = True
        return True
    else:
        GIT_SYNC_STATUS = False
        return False

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
    Guarda un alumno (Crear o Actualizar).
    - Valida duplicidad de nombre.
    - Regenera automáticamente la lista check-http basándose en el catálogo.
    """
    if not os.path.exists(ALUMNOS_FILE) and not isinstance(load_alumnos(), list):
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
            # Formato requerido: http://<app>-service.<alumno>.svc.cluster.local:<port>
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
    new_alumnos = [a for a in alumnos if str(a.get('id')) != str(student_id)]
    
    if len(new_alumnos) == initial_count:
        return False, "Alumno no encontrado."
        
    try:
        with open(ALUMNOS_FILE, "w", encoding="utf-8") as f:
             yaml.safe_dump(new_alumnos, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return True, "Alumno eliminado correctamente."
    except Exception as exc:
        return False, f"Error al borrar: {str(exc)}"


def validate_and_save_raw_yaml(raw_text: str) -> tuple[bool, str]:
    """
    Valida el texto YAML introducido manualmente en el editor y lo guarda.
    Verifica sintaxis, duplicados, claves foráneas (catálogo) y formato check-http.
    """
    # 1. Validación de Sintaxis YAML
    try:
        data = yaml.safe_load(raw_text)
    except yaml.YAMLError as e:
        return False, f"Error de sintaxis YAML: {str(e)}"

    if data is None: 
        data = []
    
    if not isinstance(data, list):
        return False, "El YAML debe ser una lista de alumnos."

    # 2. Cargar catálogo para validaciones
    servicios = load_catalogo()
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

        # A. Validar ID
        sid = str(alumno.get('id', '')).strip()
        if not sid:
            return False, f"El alumno #{idx+1} no tiene ID."
        if sid in seen_ids:
            return False, f"ID duplicado encontrado: {sid}"
        seen_ids.add(sid)

        # B. Validar Nombre
        nombre = str(alumno.get('nombre', '')).strip()
        if not nombre:
            return False, f"El alumno con ID {sid} no tiene nombre."
        if nombre.lower() in seen_names:
            return False, f"Nombre duplicado encontrado: {nombre}"
        seen_names.add(nombre.lower())

        # C. Validar Apps
        apps = alumno.get('apps', [])
        if not isinstance(apps, list):
            return False, f"La lista 'apps' del alumno {nombre} es inválida."
        
        for app in apps:
            if app not in valid_apps_ports:
                return False, f"La aplicación '{app}' asignada a {nombre} no existe en el catálogo."

        # D. Validar Check-HTTP (Consistencia Estricta)
        expected_urls = set()
        for app in apps:
            port = valid_apps_ports[app]
            url = f"http://{app}-service.{nombre}.svc.cluster.local:{port}"
            expected_urls.add(url)
        
        current_urls = set(alumno.get('check-http', []))
        
        if current_urls != expected_urls:
            return False, f"Error en 'check-http' para {nombre}. Las URLs no coinciden con las apps asignadas."

    # 4. Guardar
    try:
        with open(ALUMNOS_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return True, "Fichero YAML validado y guardado correctamente."
    except Exception as e:
        return False, f"Error de escritura: {str(e)}"

def push_alumnos_to_gitea(commit_message: str = "Update alumnos.yaml from EduGitOps App") -> tuple[bool, str]:
    """
    Sube el contenido actual de alumnos.yaml local al repositorio Gitea.
    """
    # 1. Leer contenido local (Usa la ruta local definida al inicio del archivo)
    content_yaml = get_raw_alumnos_yaml()
    if not content_yaml:
        return False, "El fichero local alumnos.yaml está vacío o no existe."

    # 2. Configurar URL usando la RUTA REMOTA
    # MODIFICACIÓN: Usamos GITEA_FILE_PATH_REMOTE para apuntar a edugitops/alumnos.yaml
    api_url = f"{config.GITEA_API_URL}/repos/{config.GITEA_REPO_OWNER}/{config.GITEA_REPO_NAME}/contents/{config.GITEA_FILE_PATH_REMOTE}"
    
    # --- DEBUG ---
    print(f"DEBUG: Intentando conectar a: {api_url}")
    print(f"DEBUG: Branch configurada: {config.GITEA_BRANCH}")
    # -------------

    auth_creds = (config.GITEA_USER, config.GITEA_PASSWORD)

    try:
        # 3. Obtener SHA del archivo remoto
        params = {'ref': config.GITEA_BRANCH}
        
        print("DEBUG: Solicitando SHA actual...")
        response_get = requests.get(api_url, auth=auth_creds, params=params, timeout=5)
        
        sha = None
        
        if response_get.status_code == 200:
            data_json = response_get.json()
            sha = data_json.get('sha')
            print(f"DEBUG: SHA encontrado: {sha}")
        elif response_get.status_code == 404:
            print("DEBUG: Archivo no encontrado en remoto (Se creará uno nuevo).")
        else:
            return False, f"Error al consultar Gitea ({response_get.status_code}): {response_get.text}"

        # 4. Codificar contenido en Base64
        content_encoded = base64.b64encode(content_yaml.encode('utf-8')).decode('utf-8')

        # 5. Preparar Payload
        data = {
            "content": content_encoded,
            "message": commit_message,
            "branch": config.GITEA_BRANCH,
        }
        
        if sha:
            data["sha"] = sha

        # 6. Enviar PUT (Push)
        print("DEBUG: Enviando PUT...")
        response_put = requests.put(api_url, auth=auth_creds, json=data, timeout=10)

        if response_put.status_code in [200, 201]:
            print("DEBUG: Push exitoso.")
            return True, "Push realizado con éxito a Gitea."
        else:
            return False, f"Error en Push ({response_put.status_code}): {response_put.text}"

    except Exception as e:
        print(f"DEBUG: Excepción General: {e}")
        return False, f"Error inesperado: {str(e)}"