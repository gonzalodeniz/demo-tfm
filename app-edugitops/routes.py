from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, render_template, request
from flask.typing import ResponseReturnValue

import data_manager

# Definimos el Blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index() -> ResponseReturnValue:
    # 1. Cargar datos usando la capa de datos
    alumnos: list[dict[str, Any]] = data_manager.load_alumnos()
    servicios: list[dict[str, Any]] = data_manager.load_catalogo()

    # 2. Lógica de selección de alumno
    selected_id: str | None = request.args.get("id")
    current_student: dict[str, Any] | None = None

    if selected_id:
        current_student = next((a for a in alumnos if str(a.get('id')) == selected_id), None)

    # Fallback
    if not current_student and alumnos:
        current_student = alumnos[0]
        
    # Objeto vacío de seguridad
    if not current_student:
        current_student = {'nombre': 'No Asignado', 'id': 'N/A', 'apps': []}

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

@main_bp.route('/save_student', methods=['POST'])
def save_student() -> ResponseReturnValue:
    data: Any = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "message": "JSON inválido."}), 400

    student_id: Any = data.get("id")
    if not isinstance(student_id, (str, int)):
        return jsonify({"success": False, "message": "El campo 'id' es obligatorio."}), 400

    new_name: Any = data.get("nombre")
    new_apps_raw: Any = data.get("apps", [])
    new_apps: list[str] = []
    if isinstance(new_apps_raw, list):
        new_apps = [str(app_id) for app_id in new_apps_raw]

    # Validación básica
    if not isinstance(new_name, str) or not new_name.strip():
        return jsonify({'success': False, 'message': 'El nombre no puede estar vacío.'}), 400

    # Delegar la lógica de negocio al data_manager
    success, message = data_manager.save_alumno_changes(student_id, new_name, new_apps)

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        # Podríamos afinar el código de estado (404 vs 500) según el mensaje, 
        # pero para simplificar usamos 500 si falla o 404 si no encuentra archivo.
        return jsonify({'success': False, 'message': message}), 400
