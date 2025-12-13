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

@patch('data_manager.load_alumnos')
@patch('data_manager.load_catalogo')
def test_index_empty_state(mock_catalogo: Any, mock_alumnos: Any, client: FlaskClient) -> None:
    """Si no hay alumnos, la cabecera de detalles debe estar vacía."""
    mock_alumnos.return_value = [] # Lista vacía
    mock_catalogo.return_value = []

    response = client.get('/')
    html = response.data.decode('utf-8')

    assert response.status_code == 200
    # Verificamos que el span esté vacío o contenga solo espacios
    # Buscamos la estructura HTML generada
    assert '<span id="header-student-name"></span>' in html or '<span id="header-student-name"> </span>' in html 
    assert 'Detalles y Asignación:' in html


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


# === TESTS DE BORRADO ===

@patch('data_manager.load_alumnos')
@patch('builtins.open', new_callable=mock_open)
@patch('yaml.safe_dump')
@patch('os.path.exists', return_value=True)
def test_delete_student_logic(
    mock_exists: Any,
    mock_dump: Any,
    mock_file: Any,
    mock_load: Any
) -> None:
    """Verifica la lógica de borrado en data_manager."""
    mock_load.return_value = [
        {'id': '001', 'nombre': 'borrar'},
        {'id': '002', 'nombre': 'quedar'}
    ]

    success, msg = data_manager.delete_student('001')
    
    assert success is True
    
    # Verificar que se guardó la lista SIN el 001
    args, _ = mock_dump.call_args
    lista_guardada = args[0]
    assert len(lista_guardada) == 1
    assert lista_guardada[0]['id'] == '002'

@patch('data_manager.delete_student')
@patch('data_manager.load_alumnos') # Para calcular next_id
def test_delete_route_redirects(
    mock_load: Any, 
    mock_delete: Any, 
    client: FlaskClient
) -> None:
    """Verifica que la ruta devuelve el next_id correcto."""
    mock_delete.return_value = (True, "Borrado")
    # Simulamos que queda un alumno
    mock_load.return_value = [{'id': '005'}] 
    
    response = client.post('/delete_student', json={'id': '001'})
    
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['next_id'] == '005'

@patch('data_manager.delete_student')
@patch('data_manager.load_alumnos')
def test_delete_route_empty_list(
    mock_load: Any, 
    mock_delete: Any, 
    client: FlaskClient
) -> None:
    """Verifica que next_id es null si no quedan alumnos."""
    mock_delete.return_value = (True, "Borrado")
    mock_load.return_value = [] # Lista vacía
    
    response = client.post('/delete_student', json={'id': '001'})
    
    assert response.status_code == 200
    assert response.json['next_id'] is None

# ====================================================================
# BLOQUE 3: Tests Editor RAW (Validaciones)
# ====================================================================

@patch('data_manager.load_catalogo')
def test_validate_raw_yaml_success(mock_catalogo: Any) -> None:
    """Debe permitir guardar si el YAML cumple todas las reglas."""
    mock_catalogo.return_value = [{'id': 'app1', 'port': 80}]
    
    # YAML válido
    raw_valid = """
- nombre: user1
  id: '001'
  apps: ['app1']
  check-http:
  - http://app1-service.user1.svc.cluster.local:80
    """
    
    # Mockeamos escritura real para no tocar disco
    with patch('builtins.open', mock_open()), patch('yaml.safe_dump'):
        success, msg = data_manager.validate_and_save_raw_yaml(raw_valid)
    
    assert success is True
    assert "correctamente" in msg

@patch('data_manager.load_catalogo')
def test_validate_raw_yaml_duplicates(mock_catalogo: Any) -> None:
    """Debe fallar si hay IDs duplicados."""
    mock_catalogo.return_value = []
    
    raw_dup = """
- nombre: u1
  id: '001'
- nombre: u2
  id: '001'
    """
    success, msg = data_manager.validate_and_save_raw_yaml(raw_dup)
    assert success is False
    assert "ID duplicado" in msg

@patch('data_manager.load_catalogo')
def test_validate_raw_yaml_invalid_app(mock_catalogo: Any) -> None:
    """Debe fallar si la app no está en el catálogo."""
    mock_catalogo.return_value = [{'id': 'app1', 'port': 80}]
    
    raw_bad_app = """
- nombre: u1
  id: '001'
  apps: ['app_inexistente']
    """
    success, msg = data_manager.validate_and_save_raw_yaml(raw_bad_app)
    assert success is False
    assert "no existe en el catálogo" in msg

@patch('data_manager.load_catalogo')
def test_validate_raw_yaml_bad_url(mock_catalogo: Any) -> None:
    """Debe fallar si la URL no coincide con el formato esperado."""
    mock_catalogo.return_value = [{'id': 'app1', 'port': 80}]
    
    raw_bad_url = """
- nombre: u1
  id: '001'
  apps: ['app1']
  check-http:
  - http://url-inventada.com
    """
    success, msg = data_manager.validate_and_save_raw_yaml(raw_bad_url)
    assert success is False
    assert "URLs no coinciden" in msg