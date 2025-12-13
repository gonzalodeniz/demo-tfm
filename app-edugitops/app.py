import os
import yaml
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- Configuración de Rutas ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALUMNOS_FILE = os.path.join(BASE_DIR, 'alumnos.yaml')
CATALOGO_FILE = os.path.join(BASE_DIR, 'catalogo-servicios.yaml')

def load_yaml_data(filepath, file_description="archivo"):
    """Carga un archivo YAML de forma segura."""
    if not os.path.exists(filepath):
        print(f"ERROR: El archivo {filepath} no existe.")
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or []
    except Exception as e:
        print(f"ERROR al cargar {file_description}: {e}")
        return []

@app.route('/')
def index():
    # 1. Cargar datos
    alumnos = load_yaml_data(ALUMNOS_FILE, "Alumnos")
    servicios = load_yaml_data(CATALOGO_FILE, "Catálogo de Servicios")

    # 2. Detectar alumno
    selected_id = request.args.get('id')
    current_student = None

    if selected_id:
        current_student = next((a for a in alumnos if str(a.get('id')) == selected_id), None)

    if not current_student and alumnos:
        current_student = alumnos[0]
        
    if not current_student:
        current_student = {'nombre': 'No Asignado', 'id': 'N/A', 'apps': []}

    # 3. Preparar datos
    assigned_apps = set(current_student.get('apps', []))

    return render_template(
        'index.html',
        alumnos=alumnos,
        servicios=servicios,
        current_student=current_student,
        assigned_apps=assigned_apps
    )

@app.route('/save_student', methods=['POST'])
def save_student():
    data = request.get_json()
    
    student_id = data.get('id')
    new_name = data.get('nombre')
    new_apps = data.get('apps', [])

    # Validación básica
    if not new_name or not new_name.strip():
        return jsonify({'success': False, 'message': 'El nombre no puede estar vacío.'}), 400

    if not os.path.exists(ALUMNOS_FILE):
        return jsonify({'success': False, 'message': 'Archivo de alumnos no encontrado.'}), 404

    try:
        # 1. Cargar datos actuales
        with open(ALUMNOS_FILE, 'r', encoding='utf-8') as f:
            alumnos_data = yaml.safe_load(f) or []

        # 2. Cargar catálogo para obtener los puertos
        # Creamos un diccionario { 'grafana': 3000, 'prometheus': 9090, ... }
        servicios_data = load_yaml_data(CATALOGO_FILE, "Catálogo")
        service_ports = {s['id']: s['port'] for s in servicios_data if 'port' in s}

        # 3. Buscar y actualizar alumno
        student_found = False
        for alumno in alumnos_data:
            if str(alumno.get('id')) == str(student_id):
                # Actualizar campos básicos
                alumno['nombre'] = new_name
                alumno['apps'] = new_apps
                
                # --- NUEVA LÓGICA: Regenerar check-http ---
                new_check_http = []
                for app_id in new_apps:
                    # Obtenemos el puerto del catálogo. Si no existe, por defecto 80 (o saltar)
                    port = service_ports.get(app_id)
                    if port:
                        # Formato: http://<app>-service.<nombre-alumno>.svc.cluster.local:<port>
                        url = f"http://{app_id}-service.{new_name}.svc.cluster.local:{port}"
                        new_check_http.append(url)
                
                alumno['check-http'] = new_check_http
                # ------------------------------------------

                student_found = True
                break
        
        if not student_found:
            return jsonify({'success': False, 'message': 'Alumno no encontrado.'}), 404

        # 4. Sobrescribir YAML
        with open(ALUMNOS_FILE, 'w', encoding='utf-8') as f:
            yaml.safe_dump(alumnos_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return jsonify({'success': True, 'message': 'Cambios guardados localmente en alumnos.yaml.'})

    except Exception as e:
        print(f"Error al guardar: {e}")
        return jsonify({'success': False, 'message': f'Error interno: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)