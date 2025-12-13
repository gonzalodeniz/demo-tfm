import pytest
import sys
import os
from unittest.mock import patch, mock_open, MagicMock

# --- Configuración de rutas ---
# Ajustamos el path para poder importar los módulos desde el directorio padre
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# IMPORTANTE: Importamos create_app en lugar de 'app'
from app import create_app
import data_manager 

# --- Fixture Global ---
@pytest.fixture
def client():
    """Configura un cliente de pruebas de Flask usando la factoría create_app."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# ====================================================================
# BLOQUE 1: Tests de Rutas (Web / Blueprint)
# Mockeamos data_manager para probar solo la respuesta HTTP
# ====================================================================

@patch('data_manager.load_alumnos')
@patch('data_manager.load_catalogo')
def test_index_route(mock_catalogo, mock_alumnos, client):
    """La ruta '/' debe cargar y mostrar los datos correctamente."""
    
    # Simulamos datos
    mock_alumnos.return_value = [
        {'nombre': 'Test Alumno', 'id': '001', 'apps': []}
    ]
    mock_catalogo.return_value = [
        {'nombre': 'Grafana', 'id': 'grafana', 'port': 3000}
    ]

    response = client.get('/')
    html = response.data.decode('utf-8')

    assert response.status_code == 200
    assert 'Test Alumno' in html
    assert 'Grafana' in html

@patch('data_manager.save_alumno_changes')
def test_save_route_success(mock_save, client):
    """La ruta POST /save_student debe llamar al manager y devolver éxito."""
    
    # Simulamos que el manager guardó todo bien
    mock_save.return_value = (True, "Guardado OK")
    
    payload = {
        'id': '001',
        'nombre': 'Nuevo Nombre',
        'apps': ['grafana']
    }
    
    response = client.post('/save_student', json=payload)
    
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['message'] == "Guardado OK"
    
    # Verificamos que se llamó a la función del manager con los datos correctos
    mock_save.assert_called_once_with('001', 'Nuevo Nombre', ['grafana'])

@patch('data_manager.save_alumno_changes')
def test_save_route_fail(mock_save, client):
    """Si el manager falla, la ruta debe devolver error."""
    
    # Simulamos error en el manager (ej. archivo no encontrado)
    mock_save.return_value = (False, "Error grave")
    
    payload = {'id': '001', 'nombre': 'X', 'apps': []}
    response = client.post('/save_student', json=payload)
    
    assert response.status_code == 400
    assert response.json['success'] is False

# ====================================================================
# BLOQUE 2: Tests de Lógica de Datos (data_manager.py)
# Aquí probamos la generación de URLs y escritura de ficheros
# ====================================================================

@patch('data_manager.load_alumnos')
@patch('data_manager.load_catalogo')
@patch('builtins.open', new_callable=mock_open)
@patch('yaml.safe_dump')
@patch('os.path.exists', return_value=True)
def test_data_manager_logic_check_http(mock_exists, mock_dump, mock_file, mock_catalogo, mock_alumnos):
    """
    Verifica la lógica interna de save_alumno_changes:
    Debe generar correctamente las URLs check-http basándose en los puertos.
    """
    
    # 1. Datos simulados que "lee" del disco
    mock_alumnos.return_value = [
        {'nombre': 'alumno-test', 'id': '999', 'apps': [], 'check-http': []}
    ]
    # El catálogo define que 'mi-app' usa el puerto 5000
    mock_catalogo.return_value = [
        {'id': 'mi-app', 'port': 5000}
    ]

    # 2. Ejecutamos la función a probar
    success, msg = data_manager.save_alumno_changes('999', 'alumno-test', ['mi-app'])
    
    assert success is True
    
    # 3. Verificamos qué se intentó escribir en el YAML
    args, _ = mock_dump.call_args
    datos_guardados = args[0]
    alumno_modificado = datos_guardados[0]
    
    # Validaciones clave
    assert len(alumno_modificado['apps']) == 1
    assert 'mi-app' in alumno_modificado['apps']
    
    # Verificamos la URL generada dinámicamente
    # Formato esperado: http://<app>-service.<alumno>.svc.cluster.local:<port>
    url_esperada = "http://mi-app-service.alumno-test.svc.cluster.local:5000"
    
    assert len(alumno_modificado['check-http']) == 1
    assert alumno_modificado['check-http'][0] == url_esperada