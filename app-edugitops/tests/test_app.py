from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
import sys
import os
from unittest.mock import patch, mock_open
from flask.testing import FlaskClient

# Ajustamos el path para poder importar los módulos desde el directorio padre
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
import data_manager 

# --- Fixture Global ---
@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Configura un cliente de pruebas de Flask usando la factoría create_app."""
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        yield test_client

# ====================================================================
# BLOQUE 1: Tests de Rutas (Web / Blueprint)
# ====================================================================

@patch('data_manager.load_alumnos')
@patch('data_manager.load_catalogo')
def test_index_route(mock_catalogo: Any, mock_alumnos: Any, client: FlaskClient) -> None:
    """La ruta '/' debe cargar y mostrar los datos correctamente."""
    mock_alumnos.return_value = [{'nombre': 'Test Alumno', 'id': '001', 'apps': []}]
    mock_catalogo.return_value = [{'nombre': 'Grafana', 'id': 'grafana', 'port': 3000}]

    response = client.get('/')
    html = response.data.decode('utf-8')

    assert response.status_code == 200
    assert 'Test Alumno' in html
    assert 'Grafana' in html

@patch('data_manager.save_alumno_changes')
def test_save_route_success(mock_save: Any, client: FlaskClient) -> None:
    """La ruta POST /save_student debe llamar al manager y devolver éxito."""
    mock_save.return_value = (True, "Guardado OK")
    
    payload = {'id': '001', 'nombre': 'Nuevo Nombre', 'apps': ['grafana']}
    response = client.post('/save_student', json=payload)
    
    assert response.status_code == 200
    assert response.json['success'] is True
    
    mock_save.assert_called_once_with('001', 'Nuevo Nombre', ['grafana'])

@patch('data_manager.load_alumnos')
def test_next_id_endpoint(mock_load_alumnos: Any, client: FlaskClient) -> None:
    """La ruta GET /next_id debe devolver el siguiente ID en JSON."""
    mock_load_alumnos.return_value = [{'id': '009'}]
    response = client.get('/next_id')
    
    assert response.status_code == 200
    assert response.json['next_id'] == "010"

# ====================================================================
# BLOQUE 2: Tests de Lógica de Negocio (data_manager.py)
# ====================================================================

@patch('data_manager.load_alumnos')
def test_next_id_logic(mock_load_alumnos: Any) -> None:
    """Verifica que calcula el siguiente ID correctamente."""
    mock_load_alumnos.return_value = [{'id': '001'}, {'id': '003'}]
    # El máximo es 3, el siguiente debe ser 004
    next_id = data_manager.get_next_student_id()
    assert next_id == "004"

@patch('data_manager.load_alumnos')
@patch('data_manager.load_catalogo')
@patch('builtins.open', new_callable=mock_open)
@patch('yaml.safe_dump')
@patch('os.path.exists', return_value=True)
def test_save_creates_new_student(
    mock_exists: Any,
    mock_dump: Any,
    mock_file: Any,
    mock_catalogo: Any,
    mock_alumnos: Any
) -> None:
    """Si el ID no existe, debe CREAR un nuevo registro."""
    # Estado inicial: solo existe el 001
    mock_alumnos.return_value = [{'nombre': 'juan', 'id': '001', 'apps': []}]
    mock_catalogo.return_value = []

    # Guardamos uno con ID 002 (nuevo)
    success, msg = data_manager.save_alumno_changes('002', 'pedro', [])
    
    assert success is True
    assert "creado" in msg.lower()

    # Verificar que se añadió a la lista para guardar
    args, _ = mock_dump.call_args
    datos_guardados = args[0]
    assert len(datos_guardados) == 2
    assert datos_guardados[1]['nombre'] == 'pedro'
    assert datos_guardados[1]['id'] == '002'

@patch('data_manager.load_alumnos')
@patch('data_manager.load_catalogo')
@patch('os.path.exists', return_value=True)
def test_save_duplicate_name_error(
    mock_exists: Any,
    mock_catalogo: Any,
    mock_alumnos: Any
) -> None:
    """Debe fallar si intentamos crear/actualizar con un nombre que ya usa otro ID."""
    mock_alumnos.return_value = [{'nombre': 'juan', 'id': '001'}]
    mock_catalogo.return_value = []

    # Intentamos crear ID 002 pero con nombre 'Juan' (duplicado)
    success, msg = data_manager.save_alumno_changes('002', 'JUAN', [])
    
    assert success is False
    assert "ya está en uso" in msg

@patch('data_manager.load_alumnos')
@patch('data_manager.load_catalogo')
@patch('builtins.open', new_callable=mock_open)
@patch('yaml.safe_dump')
@patch('os.path.exists', return_value=True)
def test_data_manager_url_generation(
    mock_exists: Any,
    mock_dump: Any,
    mock_file: Any,
    mock_catalogo: Any,
    mock_alumnos: Any,
) -> None:
    """Verifica que se generen correctamente las URLs check-http."""
    mock_alumnos.return_value = [{'nombre': 'test', 'id': '001', 'apps': []}]
    mock_catalogo.return_value = [{'id': 'mi-app', 'port': 5000}]

    success, msg = data_manager.save_alumno_changes('001', 'test', ['mi-app'])
    
    assert success is True
    
    # Verificar escritura
    args, _ = mock_dump.call_args
    datos = args[0]
    alumno = datos[0]
    
    url_esperada = "http://mi-app-service.test.svc.cluster.local:5000"
    assert len(alumno['check-http']) == 1
    assert alumno['check-http'][0] == url_esperada