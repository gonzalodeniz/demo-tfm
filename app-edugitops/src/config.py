import os

# Configuración de Gitea
# Puedes cambiar estos valores o usar variables de entorno
GITEA_API_URL = os.getenv("GITEA_API_URL", "http://localhost:3000/api/v1")
GITEA_REPO_OWNER = os.getenv("GITEA_REPO_OWNER", "admin")
GITEA_REPO_NAME = os.getenv("GITEA_REPO_NAME", "demo-tfm")
GITEA_FILE_PATH = "app-edugitops/alumnos.yaml"
GITEA_BRANCH = os.getenv("GITEA_BRANCH", "main")

# Credenciales
GITEA_USER = os.getenv("GITEA_USER", "admin")
GITEA_PASSWORD = os.getenv("GITEA_PASSWORD", "admin123")

# Configuración de la Aplicación Flask
FLASK_PORT = int(os.getenv("FLASK_PORT", 5001))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")