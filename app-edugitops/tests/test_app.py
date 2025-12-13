import pytest
import sys
import os
from unittest.mock import patch, mock_open, MagicMock
import yaml

# --- Configuración de rutas ---
# Ajustamos el path para poder importar 'app' desde el directorio padre
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, load_yaml_data

# --- Fixture Global ---
@pytest.fixture
def client():
    """Configura un cliente de pruebas de Flask."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# ==========================================
# 1. Tests de Utilidades (load_yaml_data)
# ==========================================

def test_load_yaml_valid():
    """Debe cargar correctamente un YAML válido."""
    yaml_content = "- nombre: test\n  id: '001'"
    with patch("builtins.open", mock_open(read_data=yaml_content)):
        with patch("os.path.exists", return_value=True):
            result = load_yaml_data("dummy.yaml")
            assert len(result) == 1
            assert result[0]['nombre'] == 'test'

def test_load_yaml_file_not_found():
    """Debe devolver lista vacía si el archivo no existe."""
    with patch("os.path.exists", return_value=False):
        result = load_yaml_data("no_existe.yaml")
        assert result == []

# ==========================================
# 2. Tests de la Ruta Principal (GET /)
# ==========================================

@patch('app.load_yaml_data')
def test_index_default_student(mock_load_data, client):
    """Sin parámetros, debe cargar el primer alumno."""
    mock_alumnos = [
        {'nombre': 'Alumno Uno', 'id': '001', 'apps': []},
        {'nombre': 'Alumno Dos', 'id': '002', 'apps': []}
    ]
    mock_servicios = [
        {'nombre': 'Prometheus', 'id': 'prometheus', 'port': 9090}
    ]
    
    # load_yaml_data se llama 2 veces (alumnos, servicios)
    mock_load_data.side_effect = [mock_alumnos, mock_servicios]

    response = client.get('/')
    html = response.data.decode('utf-8')

    assert response.status_code == 200
    assert 'Alumno Uno' in html
    assert 'value="001"' in html  # Verifica el ID en el input

@patch('app.load_yaml_data')
def test_switch_student_via_param(mock_load_data, client):
    """Al pasar ?id=002, debe cargar al Alumno Dos."""
    mock_alumnos = [
        {'nombre': 'Alumno Uno', 'id': '001', 'apps': []},
        {'nombre': 'Alumno Dos', 'id': '002', 'apps': ['prometheus']}
    ]
    mock_servicios = [
        {'nombre': 'Prometheus', 'id': 'prometheus', 'port': 9090}
    ]
    mock_load_data.side_effect = [mock_alumnos, mock_servicios]

    response = client.get('/?id=002')
    html = response.data.decode('utf-8')

    assert response.status_code == 200
    assert 'Alumno Dos' in html
    assert 'value="002"' in html

@patch('app.load_yaml_data')
def test_invalid_student_id_fallback(mock_load_data, client):
    """Si el ID no existe, debe hacer fallback al primero."""
    mock_alumnos = [{'nombre': 'Alumno Uno', 'id': '001'}]
    mock_load_data.side_effect = [mock_alumnos, []]

    response = client.get('/?id=999')
    html = response.data.decode('utf-8')

    assert 'Alumno Uno' in html

# ==========================================
# 3. Tests de Guardado (POST /save_student)
# ==========================================

@patch('app.load_yaml_data')  # Mockeamos carga del catálogo (para puertos)
@patch('app.yaml.safe_dump')  # Mockeamos escritura del YAML
@patch('builtins.open', new_callable=mock_open) # Mockeamos lectura/escritura archivo físico
@patch('app.yaml.safe_load')  # Mockeamos lectura de alumnos.yaml
@patch('os.path.exists', return_value=True)
def test_save_student_check_http_generation(mock_exists, mock_yaml_load_alumnos, mock_file, mock_yaml_dump, mock_load_catalogo, client):
    """
    Verifica que al guardar:
    1. Se actualizan apps y nombre.
    2. Se genera correctamente la lista check-http usando los puertos del catálogo.
    """
    
    # 1. ESTADO INICIAL (Lo que hay en alumnos.yaml antes de guardar)
    mock_yaml_load_alumnos.return_value = [
        {'nombre': 'alumno-juan', 'id': '001', 'apps': ['prometheus'], 'check-http': []}
    ]

    # 2. CATALOGO DE SERVICIOS (Lo que lee app.py para saber los puertos)
    # Importante: save_student llama a load_yaml_data para esto.
    mock_load_catalogo.return_value = [
        {'id': 'prometheus', 'port': 9090},
        {'id': 'grafana', 'port': 3000}
    ]

    # 3. DATOS ENVIADOS DESDE EL FRONTEND (Lo que el usuario cambió)
    # El usuario añade 'grafana' a la lista.
    payload = {
        'id': '001',
        'nombre': 'alumno-juan',
        'apps': ['prometheus', 'grafana'] 
    }

    # 4. EJECUCIÓN
    response = client.post('/save_student', json=payload)
    
    # 5. ASERCIONES HTTP
    assert response.status_code == 200
    assert response.json['success'] is True
    
    # 6. ASERCIONES DE DATOS (Lo que se intentó escribir en el disco)
    # Obtenemos los argumentos con los que se llamó a safe_dump
    args, _ = mock_yaml_dump.call_args
    datos_guardados = args[0]
    alumno_actualizado = datos_guardados[0]

    # A. Verificar nombre y apps
    assert alumno_actualizado['nombre'] == 'alumno-juan'
    assert len(alumno_actualizado['apps']) == 2
    
    # B. Verificar URLs generadas (check-http)
    # Deben coincidir con el formato: http://<app>-service.<alumno>.svc.cluster.local:<port>
    urls_esperadas = [
        "http://prometheus-service.alumno-juan.svc.cluster.local:9090",
        "http://grafana-service.alumno-juan.svc.cluster.local:3000"
    ]
    
    assert len(alumno_actualizado['check-http']) == 2
    # Verificamos que las URLs esperadas estén presentes
    for url in urls_esperadas:
        assert url in alumno_actualizado['check-http']

def test_save_student_empty_name(client):
    """Prueba que rechaza guardar si el nombre está vacío."""
    payload = {'id': '001', 'nombre': '', 'apps': []}
    
    response = client.post('/save_student', json=payload)
    
    assert response.status_code == 400
    assert response.json['success'] is False
    assert 'nombre' in response.json['message']