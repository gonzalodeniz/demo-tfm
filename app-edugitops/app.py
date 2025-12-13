from __future__ import annotations

from flask import Flask
from routes import main_bp

def create_app() -> Flask:
    app = Flask(__name__)
    
    # Registrar el Blueprint con las rutas
    app.register_blueprint(main_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
