from flask import Blueprint, render_template, request, jsonify
import data_manager

# Definimos el Blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # 1. Cargar datos usando la capa de datos
    alumnos = data_manager.load_alumnos()
    servicios = data_manager.load_catalogo()

    # 2. Lógica de selección de alumno
    selected_id = request.args.get('id')
    current_student = None

    if selected_id:
        current_student = next((a for a in alumnos if str(a.get('id')) == selected_id), None)

    # Fallback
    if not current_student and alumnos:
        current_student = alumnos[0]
        
    # Objeto vacío de seguridad
    if not current_student:
        current_student = {'nombre': 'No Asignado', 'id': 'N/A', 'apps': []}

    assigned_apps = set(current_student.get('apps', []))

    return render_template(
        'index.html',
        alumnos=alumnos,
        servicios=servicios,
        current_student=current_student,
        assigned_apps=assigned_apps
    )

@main_bp.route('/save_student', methods=['POST'])
def save_student():
    data = request.get_json()
    
    student_id = data.get('id')
    new_name = data.get('nombre')
    new_apps = data.get('apps', [])

    # Validación básica
    if not new_name or not new_name.strip():
        return jsonify({'success': False, 'message': 'El nombre no puede estar vacío.'}), 400

    # Delegar la lógica de negocio al data_manager
    success, message = data_manager.save_alumno_changes(student_id, new_name, new_apps)

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        # Podríamos afinar el código de estado (404 vs 500) según el mensaje, 
        # pero para simplificar usamos 500 si falla o 404 si no encuentra archivo.
        return jsonify({'success': False, 'message': message}), 400