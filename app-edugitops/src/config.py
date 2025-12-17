import os
import os.path

# --- CONFIGURACIÓN GITEA ---
GITEA_API_URL = os.getenv("GITEA_API_URL", "http://localhost:3000/api/v1")
GITEA_REPO_OWNER = os.getenv("GITEA_REPO_OWNER", "admin")
GITEA_REPO_NAME = os.getenv("GITEA_REPO_NAME", "demo-tfm")
GITEA_BRANCH = os.getenv("GITEA_BRANCH", "gonzalo")
GITEA_USER = os.getenv("GITEA_USER", "admin")
GITEA_PASSWORD = os.getenv("GITEA_PASSWORD", "admin123")

# --- RUTAS REMOTAS (Para la API de Gitea - Git/ArgoCD) ---
# Estas deben coincidir con la estructura de carpetas en tu repositorio Git.
# Por defecto: "edugitops/alumnos.yaml"
GITEA_FILE_PATH_REMOTE = os.getenv("GITEA_FILE_PATH", "edugitops/alumnos.yaml")
GITEA_CATALOGO_PATH_REMOTE = os.getenv("GITEA_CATALOGO_PATH", "edugitops/catalogo-servicios.yaml")

# Mantenemos compatibilidad hacia atrás por si algo más lo usa, 
# pero data_manager usará las versiones _REMOTE explícitas.
GITEA_FILE_PATH = GITEA_FILE_PATH_REMOTE
GITEA_CATALOGO_PATH = GITEA_CATALOGO_PATH_REMOTE

# --- CONFIGURACIÓN FLASK ---
FLASK_PORT = int(os.getenv("FLASK_PORT", 5001))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")