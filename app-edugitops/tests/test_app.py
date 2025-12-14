from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
import sys
import os
# CORRECCIÓN AQUÍ: Añadido MagicMock a la importación
from unittest.mock import patch, mock_open, MagicMock
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
    mock_alumnos.return_value = []
    mock_catalogo.return_value = []

    response = client.get('/')
    html = response.data.decode('utf-8')

    assert response.status_code == 200
    # Verificamos que el span esté vacío o contenga solo espacios
    assert '<span id="header-student-name"></span>' in html or '<span id="header-student-name"> </span>' in html 

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
# BLOQUE 2: Tests de Lógica de Negocio (CRUD y Validaciones)
# ====================================================================

@patch('data_manager.load_alumnos')
def test_next_id_logic(mock_load_alumnos: Any) -> None:
    """Verifica que calcula el siguiente ID correctamente."""
    mock_load_alumnos.return_value = [{'id': '001'}, {'id': '003'}]
    next_id = data_manager.get_next_student_id()
    assert next_id == "004"

@patch('data_manager.load_alumnos')
@patch('data_manager.load_catalogo')
@patch('builtins.open', new_callable=mock_open)
@patch('yaml.safe_dump')
@patch('os.path.exists', return_value=True)
def test_save_creates_new_student(
    mock_exists: Any, mock_dump: Any, mock_file: Any, mock_catalogo: Any, mock_alumnos: Any
) -> None:
    """Si el ID no existe, debe CREAR un nuevo registro."""
    mock_alumnos.return_value = [{'nombre': 'juan', 'id': '001', 'apps': []}]
    mock_catalogo.return_value = []

    success, msg = data_manager.save_alumno_changes('002', 'pedro', [])
    
    assert success is True
    assert "creado" in msg.lower()

    args, _ = mock_dump.call_args
    datos_guardados = args[0]
    assert len(datos_guardados) == 2
    assert datos_guardados[1]['nombre'] == 'pedro'

@patch('data_manager.load_alumnos')
@patch('data_manager.load_catalogo')
@patch('os.path.exists', return_value=True)
def test_save_duplicate_name_error(
    mock_exists: Any, mock_catalogo: Any, mock_alumnos: Any
) -> None:
    """Debe fallar si intentamos crear/actualizar con un nombre que ya usa otro ID."""
    mock_alumnos.return_value = [{'nombre': 'juan', 'id': '001'}]
    mock_catalogo.return_value = []

    success, msg = data_manager.save_alumno_changes('002', 'JUAN', [])
    
    assert success is False
    assert "ya está en uso" in msg

@patch('data_manager.load_alumnos')
@patch('data_manager.load_catalogo')
@patch('builtins.open', new_callable=mock_open)
@patch('yaml.safe_dump')
@patch('os.path.exists', return_value=True)
def test_data_manager_url_generation(
    mock_exists: Any, mock_dump: Any, mock_file: Any, mock_catalogo: Any, mock_alumnos: Any
) -> None:
    """Verifica que se generen correctamente las URLs check-http."""
    mock_alumnos.return_value = [{'nombre': 'test', 'id': '001', 'apps': []}]
    mock_catalogo.return_value = [{'id': 'mi-app', 'port': 5000}]

    success, msg = data_manager.save_alumno_changes('001', 'test', ['mi-app'])
    
    assert success is True
    
    args, _ = mock_dump.call_args
    alumno = args[0][0]
    url_esperada = "http://mi-app-service.test.svc.cluster.local:5000"
    assert alumno['check-http'][0] == url_esperada

# ====================================================================
# BLOQUE 3: Tests de Borrado
# ====================================================================

@patch('data_manager.load_alumnos')
@patch('builtins.open', new_callable=mock_open)
@patch('yaml.safe_dump')
@patch('os.path.exists', return_value=True)
def test_delete_student_logic(
    mock_exists: Any, mock_dump: Any, mock_file: Any, mock_load: Any
) -> None:
    """Verifica la lógica de borrado en data_manager."""
    mock_load.return_value = [
        {'id': '001', 'nombre': 'borrar'},
        {'id': '002', 'nombre': 'quedar'}
    ]
    success, msg = data_manager.delete_student('001')
    assert success is True
    
    args, _ = mock_dump.call_args
    lista_guardada = args[0]
    assert len(lista_guardada) == 1
    assert lista_guardada[0]['id'] == '002'

@patch('data_manager.delete_student')
@patch('data_manager.load_alumnos')
def test_delete_route_redirects(mock_load: Any, mock_delete: Any, client: FlaskClient) -> None:
    """Verifica que la ruta devuelve el next_id correcto."""
    mock_delete.return_value = (True, "Borrado")
    mock_load.return_value = [{'id': '005'}] 
    
    response = client.post('/delete_student', json={'id': '001'})
    
    assert response.status_code == 200
    assert response.json['success'] is True
    assert response.json['next_id'] == '005'

@patch('data_manager.delete_student')
@patch('data_manager.load_alumnos')
def test_delete_route_empty_list(mock_load: Any, mock_delete: Any, client: FlaskClient) -> None:
    """Verifica que next_id es null si no quedan alumnos."""
    mock_delete.return_value = (True, "Borrado")
    mock_load.return_value = [] 
    
    response = client.post('/delete_student', json={'id': '001'})
    
    assert response.status_code == 200
    assert response.json['next_id'] is None

# ====================================================================
# BLOQUE 4: Tests Editor RAW (Validaciones)
# ====================================================================

@patch('data_manager.load_catalogo')
def test_validate_raw_yaml_success(mock_catalogo: Any) -> None:
    """Debe permitir guardar si el YAML cumple todas las reglas."""
    mock_catalogo.return_value = [{'id': 'app1', 'port': 80}]
    raw_valid = """
- nombre: user1
  id: '001'
  apps: ['app1']
  check-http:
  - http://app1-service.user1.svc.cluster.local:80
    """
    with patch('builtins.open', mock_open()), patch('yaml.safe_dump'):
        success, msg = data_manager.validate_and_save_raw_yaml(raw_valid)
    assert success is True

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

# ====================================================================
# BLOQUE 5: Tests de Integración Git (Gitea)
# ====================================================================

@patch('data_manager.get_raw_alumnos_yaml')
@patch('requests.put')
@patch('requests.get')
def test_push_gitea_success(mock_get: Any, mock_put: Any, mock_read_file: Any) -> None:
    """Verifica el flujo correcto de Push (GET SHA -> PUT Content)."""
    
    # 1. Simular lectura de fichero local
    mock_read_file.return_value = "- nombre: test"

    # 2. Simular respuesta GET (Obtener SHA existente)
    mock_response_get = MagicMock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = {'sha': 'dummy_sha_123'}
    mock_get.return_value = mock_response_get

    # 3. Simular respuesta PUT (Subida exitosa)
    mock_response_put = MagicMock()
    mock_response_put.status_code = 200
    mock_put.return_value = mock_response_put

    # Ejecutar función
    success, msg = data_manager.push_alumnos_to_gitea()

    assert success is True
    assert "éxito" in msg

    # Verificar llamadas
    mock_get.assert_called_once()
    mock_put.assert_called_once()
    
    # Verificar payload del PUT
    args, kwargs = mock_put.call_args
    payload = kwargs['json']
    assert payload['sha'] == 'dummy_sha_123'
    assert 'content' in payload

@patch('data_manager.get_raw_alumnos_yaml')
@patch('requests.get')
def test_push_gitea_connection_error(mock_get: Any, mock_read_file: Any) -> None:
    """Verifica el manejo de errores de conexión."""
    import requests
    mock_read_file.return_value = "content"
    
    # Simular excepción de conexión
    mock_get.side_effect = requests.exceptions.ConnectionError("Gitea down")

    success, msg = data_manager.push_alumnos_to_gitea()

    assert success is False
    assert "Error de conexión" in msg

@patch('data_manager.push_alumnos_to_gitea')
def test_git_push_route(mock_push: Any, client: FlaskClient) -> None:
    """Verifica que la ruta responde correctamente."""
    mock_push.return_value = (True, "Push OK")
    
    response = client.post('/git_push', json={})
    
    assert response.status_code == 200
    assert response.json['success'] is True