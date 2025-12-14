FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalar dependencias base y kubectl
RUN apt-get update && apt-get install -y curl ca-certificates unzip && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/

ENV PYTHONPATH=/app/src

# Puerto por defecto (documentación)
# Nota: EXPOSE no publica el puerto, solo informa. 
# Si cambias la variable de entorno FLASK_PORT al correr el contenedor, 
# deberás exponer ese puerto nuevo con -p.
EXPOSE 5001

# Definir variables de entorno por defecto (opcional, ya están en config.py)
ENV FLASK_PORT=5001
ENV FLASK_DEBUG=True

CMD ["python", "src/app.py"]