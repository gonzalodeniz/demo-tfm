from flask import Flask
from routes import main_bp
import config
import data_manager # Importamos para ejecutar la sincro

def create_app():
    app = Flask(__name__)
    
    # Ejecutar Sincronización Inicial con Gitea
    print("--- INICIANDO SINCRONIZACIÓN CON GIT ---")
    if data_manager.sync_files_from_gitea():
        print("--- GIT: SINCRONIZADO CORRECTAMENTE ---")
    else:
        print("--- GIT: ERROR DE SINCRONIZACIÓN (Usando ficheros locales) ---")

    app.register_blueprint(main_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=config.FLASK_DEBUG, host='0.0.0.0', port=config.FLASK_PORT)