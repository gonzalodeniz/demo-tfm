import os
import yaml
from flask import Flask, render_template

app = Flask(__name__)

# --- Configuración de Rutas ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALUMNOS_FILE = os.path.join(BASE_DIR, 'alumnos.yaml')
CATALOGO_FILE = os.path.join(BASE_DIR, 'catalogo-servicios.yaml')

def load_yaml_data(filepath, file_description="archivo"):
    """
    Carga un archivo YAML con diagnósticos detallados.
    """
    print(f"--- Cargando {file_description} desde: {filepath} ---")
    
    if not os.path.exists(filepath):
        print(f"ERROR: El archivo no existe en la ruta especificada.")
        return []

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or []
            print(f"ÉXITO: Se cargaron {len(data)} elementos.")
            return data
    except yaml.YAMLError as exc:
        print(f"ERROR YAML: Error de sintaxis en {file_description}.\nDetalle: {exc}")
        return []
    except UnicodeDecodeError:
        print(f"ERROR CODIFICACIÓN: El archivo {file_description} no está guardado en UTF-8.")
        return []
    except Exception as e:
        print(f"ERROR DESCONOCIDO: {e}")
        return []

@app.route('/')
def index():
    # 1. Cargar datos con logs en terminal
    alumnos = load_yaml_data(ALUMNOS_FILE, "Alumnos")
    servicios = load_yaml_data(CATALOGO_FILE, "Catálogo de Servicios")

    # 2. Lógica de selección de alumno (Simulación)
    # Por defecto seleccionamos el ID 001 (Juan) para que coincida con el prototipo
    current_student_id = "001"
    current_student = next((a for a in alumnos if str(a.get('id')) == current_student_id), None)

    # Fallback si no existe el 001
    if not current_student and alumnos:
        current_student = alumnos[0]

    # 3. Preparar apps asignadas
    # Convertimos a set para verificar rápido en el template
    assigned_apps = set()
    if current_student and 'apps' in current_student:
        assigned_apps = set(current_student['apps'])

    return render_template(
        'index.html',
        alumnos=alumnos,
        servicios=servicios,
        current_student=current_student,
        assigned_apps=assigned_apps
    )

if __name__ == '__main__':
    print(f"Directorio base de la aplicación: {BASE_DIR}")
    app.run(debug=True, port=5000)