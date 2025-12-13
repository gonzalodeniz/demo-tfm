import os
import yaml

# Definimos rutas absolutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALUMNOS_FILE = os.path.join(BASE_DIR, 'alumnos.yaml')
CATALOGO_FILE = os.path.join(BASE_DIR, 'catalogo-servicios.yaml')

def _load_yaml(filepath):
    """Función interna para cargar YAML genérico."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or []
    except Exception as e:
        print(f"Error cargando {filepath}: {e}")
        return []

def load_alumnos():
    """Devuelve la lista de alumnos."""
    return _load_yaml(ALUMNOS_FILE)

def load_catalogo():
    """Devuelve la lista de servicios del catálogo."""
    return _load_yaml(CATALOGO_FILE)

def save_alumno_changes(student_id, new_name, new_apps):
    """
    Actualiza un alumno, regenera sus URLs check-http y guarda en disco.
    Retorna (True, mensaje) si tiene éxito, o (False, error).
    """
    if not os.path.exists(ALUMNOS_FILE):
        return False, "Archivo de alumnos no encontrado."

    try:
        # 1. Cargar datos
        alumnos_data = load_alumnos()
        servicios_data = load_catalogo()
        
        # Mapa de puertos para búsqueda rápida: {'grafana': 3000, ...}
        service_ports = {s['id']: s['port'] for s in servicios_data if 'port' in s}

        # 2. Buscar y actualizar
        student_found = False
        for alumno in alumnos_data:
            if str(alumno.get('id')) == str(student_id):
                alumno['nombre'] = new_name
                alumno['apps'] = new_apps
                
                # Lógica de negocio: Regenerar URLs check-http
                new_check_http = []
                for app_id in new_apps:
                    port = service_ports.get(app_id)
                    if port:
                        url = f"http://{app_id}-service.{new_name}.svc.cluster.local:{port}"
                        new_check_http.append(url)
                
                alumno['check-http'] = new_check_http
                student_found = True
                break
        
        if not student_found:
            return False, "Alumno no encontrado."

        # 3. Guardar en disco
        with open(ALUMNOS_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(alumnos_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return True, "Cambios guardados localmente correctamente."

    except Exception as e:
        print(f"Error al guardar: {e}")
        return False, f"Error interno: {str(e)}"