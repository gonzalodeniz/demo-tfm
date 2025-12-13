import os
import yaml
from flask import Flask, render_template, request  # <--- Importamos request

app = Flask(__name__)

# --- Configuración de Rutas ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALUMNOS_FILE = os.path.join(BASE_DIR, 'alumnos.yaml')
CATALOGO_FILE = os.path.join(BASE_DIR, 'catalogo-servicios.yaml')

def load_yaml_data(filepath, file_description="archivo"):
    """Carga un archivo YAML de forma segura y con logs."""
    # (Misma función que tenías antes, no cambia)
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

    # 2. Detectar alumno seleccionado vía URL (?id=XXX)
    selected_id = request.args.get('id')
    current_student = None

    # Intentar buscar el alumno por el ID recibido
    if selected_id:
        current_student = next((a for a in alumnos if str(a.get('id')) == selected_id), None)

    # Si no se encontró, o no se seleccionó, usamos el primero.
    if not current_student and alumnos:
        current_student = alumnos[0]
        
    # [CAMBIO CLAVE] Si NO HAY ALUMNOS, creamos un objeto vacío de seguridad 
    # para evitar fallos de Jinja2 al intentar acceder a current_student.nombre.
    if not current_student:
        current_student = {'nombre': 'No Asignado', 'id': 'N/A', 'apps': []}
        
    # 3. Preparar apps asignadas para los checkboxes
    assigned_apps = set(current_student.get('apps', [])) # Usamos .get('apps', []) para seguridad

    return render_template(
        'index.html',
        alumnos=alumnos,
        servicios=servicios,
        current_student=current_student,
        assigned_apps=assigned_apps
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)