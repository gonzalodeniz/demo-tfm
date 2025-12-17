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

# CORRECCIÓN: Rutas relativas simples (asumiendo build context = carpeta actual)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos src (donde está app.py y data_manager.py)
COPY src/ ./src/

# Copiamos los scripts de monitorización
COPY monitoring-scripts/ ./monitoring-scripts/

ENV PYTHONPATH=/app/src
ENV FLASK_PORT=5001
ENV FLASK_DEBUG=True

EXPOSE 5001

CMD ["python", "src/app.py"]