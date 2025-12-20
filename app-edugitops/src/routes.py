from __future__ import annotations

import os
import subprocess
import re
from typing import Any

from flask import Blueprint, jsonify, render_template, request
from flask.typing import ResponseReturnValue

import data_manager
import config

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index() -> ResponseReturnValue:
    # Cargar datos (puede ser local o actualizado desde git)
    alumnos: list[dict[str, Any]] = data_manager.load_alumnos()
    servicios: list[dict[str, Any]] = data_manager.load_catalogo()

    # Obtener el estado global de la sincronización con Git
    git_sync_status = data_manager.GIT_SYNC_STATUS

    selected_id: str | None = request.args.get("id")
    current_student: dict[str, Any] | None = None

    if selected_id:
        current_student = next((a for a in alumnos if str(a.get('id')) == selected_id), None)

    # Fallback: si no hay alumno seleccionado y hay alumnos en la lista
    if not current_student and alumnos and not selected_id:
         current_student = alumnos[0]

    # Objeto vacío por defecto
    if not current_student:
        current_student = {'nombre': '', 'id': '', 'apps': []}

    assigned_apps: set[str] = set()
    apps_value = current_student.get("apps", [])
    if isinstance(apps_value, list):
        assigned_apps = {str(app_id) for app_id in apps_value}

    return render_template(
        'index.html',
        alumnos=alumnos,
        servicios=servicios,
        current_student=current_student,
        assigned_apps=assigned_apps,
        git_sync_status=git_sync_status
    )

@main_bp.route('/info')
def info_route() -> ResponseReturnValue:
    """Muestra la versión y las variables de entorno (con secretos ofuscados)."""
    
    # 1. Capturamos todas las variables
    all_vars = dict(os.environ)
    
    # 2. Filtramos/Ofuscamos secretos por seguridad
    safe_vars = {}
    sensitive_keys = ['PASS', 'SECRET', 'TOKEN', 'KEY', 'PASSWORD']
    
    for key, value in sorted(all_vars.items()):
        is_sensitive = any(s in key.upper() for s in sensitive_keys)
        if is_sensitive and value:
            # Mostramos solo los primeros 3 caracteres y ocultamos el resto
            visible_part = value[:3] if len(value) > 3 else "*"
            safe_vars[key] = f"{visible_part}********"
        else:
            safe_vars[key] = value

    # Usamos la versión definida en config.py (que viene del .env)
    return render_template('info.html', version=config.APP_VERSION, env_vars=safe_vars)

@main_bp.route('/next_id', methods=['GET'])
def next_id() -> ResponseReturnValue:
    """Devuelve el siguiente ID disponible."""
    new_id = data_manager.get_next_student_id()
    return jsonify({'next_id': new_id})

@main_bp.route('/save_student', methods=['POST'])
def save_student() -> ResponseReturnValue:
    data: Any = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "JSON inválido."}), 400

    student_id: Any = data.get("id")
    new_name: Any = data.get("nombre")
    new_apps_raw: Any = data.get("apps", [])

    # Validación básica de entrada
    if not student_id:
        return jsonify({'success': False, 'message': 'El ID es obligatorio.'}), 400
    
    if not isinstance(new_name, str) or not new_name.strip():
        return jsonify({'success': False, 'message': 'El nombre no puede estar vacío.'}), 400

    new_apps: list[str] = []
    if isinstance(new_apps_raw, list):
        new_apps = [str(app_id) for app_id in new_apps_raw]

    # Delegar lógica (Crear o Actualizar)
    success, message = data_manager.save_alumno_changes(student_id, new_name, new_apps)

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@main_bp.route('/delete_student', methods=['POST'])
def delete_student() -> ResponseReturnValue:
    data: Any = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "JSON inválido."}), 400

    student_id: Any = data.get("id")
    if not student_id:
        return jsonify({'success': False, 'message': 'ID obligatorio.'}), 400
    
    success, msg = data_manager.delete_student(student_id)
    
    if success:
        # Calcular cuál es el siguiente alumno a mostrar tras el borrado
        alumnos_restantes = data_manager.load_alumnos()
        next_id = None
        if alumnos_restantes:
            next_id = alumnos_restantes[0]['id']
            
        return jsonify({'success': True, 'message': msg, 'next_id': next_id})
    else:
        return jsonify({'success': False, 'message': msg}), 400

@main_bp.route('/editor')
def editor() -> ResponseReturnValue:
    """Renderiza la vista de edición manual de YAML."""
    raw_content = data_manager.get_raw_alumnos_yaml()
    return render_template('yaml_editor.html', raw_content=raw_content)

@main_bp.route('/save_raw_yaml', methods=['POST'])
def save_raw_yaml() -> ResponseReturnValue:
    data: Any = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "JSON inválido."}), 400

    raw_text = data.get('content')
    if raw_text is None: # Puede ser string vacío
        return jsonify({"success": False, "message": "Falta el contenido."}), 400

    success, message = data_manager.validate_and_save_raw_yaml(str(raw_text))

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message}), 400

@main_bp.route('/git_push', methods=['POST'])
def git_push() -> ResponseReturnValue:
    """Ejecuta la subida del fichero a Gitea."""
    data: Any = request.get_json(silent=True)
    message = "Actualización desde EduGitOps"
    
    if isinstance(data, dict) and data.get("message"):
        message = str(data.get("message"))

    success, msg = data_manager.push_alumnos_to_gitea(commit_message=message)

    if success:
        return jsonify({'success': True, 'message': msg})
    else:
        # 502 Bad Gateway es apropiado para errores de upstream (Gitea)
        return jsonify({'success': False, 'message': msg}), 502

@main_bp.route('/sync_git', methods=['POST'])
def sync_git() -> ResponseReturnValue:
    """Fuerza un reintento de sincronización con Gitea."""
    success = data_manager.sync_files_from_gitea()
    
    if success:
        return jsonify({'success': True, 'message': 'Sincronización con Gitea exitosa.'})
    else:
        return jsonify({'success': False, 'message': 'Fallo al sincronizar. Verifique que Gitea está activo.'}), 502

def run_kubectl_command(command_list):
    """Ejecuta un comando kubectl y devuelve la salida como texto."""
    try:
        # Añadimos --kubeconfig si fuera necesario, pero asumimos que el entorno tiene acceso
        result = subprocess.check_output(command_list, text=True, stderr=subprocess.STDOUT)
        return result.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando kubectl: {e.output}")
        return None
    except FileNotFoundError:
        return None

def get_node_external_ip():
    """Obtiene la IP Externa (o Interna) del primer nodo usando kubectl."""
    # Comando equivalente a: kubectl get nodes -o wide --no-headers
    output = run_kubectl_command(['kubectl', 'get', 'nodes', '-o', 'wide', '--no-headers'])
    
    if not output:
        return "127.0.0.1"

    # Procesamos línea por línea (normalmente solo hay un nodo o varios)
    for line in output.split('\n'):
        parts = line.split()
        if len(parts) >= 7:
            # En 'get nodes -o wide', las columnas suelen ser:
            # NAME STATUS ROLES AGE VERSION INTERNAL-IP EXTERNAL-IP
            # Index 5 es Internal, Index 6 es External (normalmente)
            external_ip = parts[6] if len(parts) > 6 else "<none>"
            internal_ip = parts[5]
            
            # Si tiene IP externa real (no <none>), la usamos. Si no, la interna.
            if external_ip != "<none>":
                return external_ip
            return internal_ip
            
    return "127.0.0.1"

@main_bp.route('/deployments')
def deployments_view() -> ResponseReturnValue:
    """Vista para listar servicios NodePort de alumnos y Checkmk."""
    
    deployments_list = []
    error_msg = None
    node_ip = "127.0.0.1"

    try:
        # 1. Obtener IP del Nodo
        node_ip = get_node_external_ip()

        # 2. Obtener Servicios
        svc_output = run_kubectl_command(['kubectl', 'get', 'svc', '-A', '--no-headers'])

        if svc_output:
            for line in svc_output.split('\n'):
                # Ejemplo de línea: 
                # checkmk      checkmk               NodePort    10.100.x.x  <none>  80:30000/TCP  5m
                parts = line.split()
                
                if len(parts) >= 5:
                    namespace = parts[0]
                    name = parts[1]
                    svc_type = parts[2]
                    ports_str = parts[4] if len(parts) == 5 else parts[5]

                    # --- CAMBIO AQUÍ ---
                    # Aceptamos si es alumno O si es checkmk, Y además es NodePort
                    es_alumno = namespace.startswith('alumno-')
                    es_checkmk = (namespace == 'checkmk')

                    if (es_alumno or es_checkmk) and svc_type == 'NodePort':
                        
                        # Extraer el puerto externo (NodePort)
                        match = re.search(r':(\d+)', ports_str)
                        node_port = match.group(1) if match else "???"
                        
                        # Extraer el puerto interno (el que está antes de los :)
                        # Esto es importante porque Checkmk suele usar el 80 internamente pero expone otro
                        internal_port = ports_str.split(':')[0] if ':' in ports_str else "80"

                        # Comando para copiar
                        cmd = f"kubectl port-forward -n {namespace} svc/{name} {node_port}:{internal_port}"

                        deployments_list.append({
                            'namespace': namespace,
                            'app_name': name,
                            'node_ip': node_ip,
                            'port': node_port,
                            'url': f"http://{node_ip}:{node_port}",
                            'pf_cmd': cmd
                        })
            
            # Ordenar: primero checkmk para que salga arriba, luego los alumnos
            deployments_list.sort(key=lambda x: (0 if x['namespace'] == 'checkmk' else 1, x['namespace']))
        else:
            error_msg = "No se pudo obtener la lista de servicios."

    except Exception as e:
        error_msg = f"Error inesperado: {str(e)}"

    return render_template('deployments.html', deployments=deployments_list, error=error_msg)
    