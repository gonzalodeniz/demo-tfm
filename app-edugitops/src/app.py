from flask import Flask
from routes import main_bp
import config  # Importamos la configuración

def create_app():
    app = Flask(__name__)
    
    # Registrar el Blueprint con las rutas
    app.register_blueprint(main_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Usamos las variables de configuración
    app.run(debug=config.FLASK_DEBUG, host='0.0.0.0', port=config.FLASK_PORT)