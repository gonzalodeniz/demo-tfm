import subprocess
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>Monitor de Servicios K8s</h1>
    <p>Ruta: <a href="/services">/services</a> para ver direcciones públicas.</p>
    """

@app.route('/services')
def get_services():
    try:
        # -o wide muestra IPs externas y puertos
        cmd = ['kubectl', 'get', 'services', '--all-namespaces', '-o', 'wide']
        
        result = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        return f"<pre>{result}</pre>"
    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "Error ejecutando kubectl", 
            "output": e.output
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)