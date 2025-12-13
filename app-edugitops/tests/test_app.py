import pytest
import sys
import os
from unittest.mock import patch, mock_open
import yaml

# --- Configuración de rutas ---
# Añadimos el directorio padre al path para poder importar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, load_yaml_data

# --- Fixtures (Configuración) ---

@pytest.fixture
def client():
    """Configura un cliente de pruebas de Flask para cada test."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# --- Tests de Utilidades (Unitarios) ---

def test_load_yaml_valid():
    """Debe cargar correctamente un YAML válido."""
    yaml_content = "- nombre: test\n  id: '001'"
    
    # Mockeamos 'open' y 'os.path.exists'
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

def test_load_yaml_syntax_error():
    """Debe manejar errores de sintaxis YAML devolviendo lista vacía."""
    # Simulamos que yaml.safe_load lanza una excepción YAMLError
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="key: value")):
            # Usamos side_effect para lanzar la excepción
            with patch("yaml.safe_load", side_effect=yaml.YAMLError("Error simulado")):
                result = load_yaml_data("bad.yaml")
                assert result == []

# --- Tests de Integración (Rutas Flask) ---

@patch('app.load_yaml_data')
def test_index_route_success(mock_load_data, client):
    """La ruta '/' debe cargar y mostrar datos correctamente en el HTML."""
    
    # Datos simulados (Mocks)
    mock_alumnos = [
        {'nombre': 'Test Alumno', 'id': '001', 'apps': ['grafana']}
    ]
    mock_servicios = [
        {'nombre': 'Grafana', 'id': 'grafana', 'descripcion': 'Panel visual'}
    ]

    # Configuramos el mock para que devuelva primero alumnos, luego servicios
    mock_load_data.side_effect = [mock_alumnos, mock_servicios]

    # Realizamos la petición GET usando el fixture 'client'
    response = client.get('/')

    # 1. Verificar status code
    assert response.status_code == 200

    # 2. Verificar contenido HTML
    html_content = response.data.decode('utf-8')
    
    assert 'Test Alumno' in html_content
    assert 'Grafana' in html_content
    assert 'checked' in html_content  # El checkbox debe estar marcado

@patch('app.load_yaml_data')
def test_index_route_no_data(mock_load_data, client):
    """La ruta '/' debe funcionar incluso sin datos."""
    mock_load_data.return_value = [] # Devuelve listas vacías

    response = client.get('/')
    
    assert response.status_code == 200
    assert 'Directorio de Alumnos' in response.data.decode('utf-8')