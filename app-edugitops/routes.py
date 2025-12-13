from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, render_template, request
from flask.typing import ResponseReturnValue

import data_manager

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index() -> ResponseReturnValue:
    alumnos: list[dict[str, Any]] = data_manager.load_alumnos()
    servicios: list[dict[str, Any]] = data_manager.load_catalogo()

    selected_id: str | None = request.args.get("id")
    current_student: dict[str, Any] | None = None

    if selected_id:
        current_student = next((a for a in alumnos if str(a.get('id')) == selected_id), None)

    # Fallback normal
    if not current_student and alumnos and not selected_id:
         # Solo cargamos el primero si NO se pidió explícitamente un ID (o si es carga inicial)
         # Si se pidió un ID y no existe, podríamos mostrar vacío o el primero.
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
        assigned_apps=assigned_apps
    )

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