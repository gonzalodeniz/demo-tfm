from __future__ import annotations

import os
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