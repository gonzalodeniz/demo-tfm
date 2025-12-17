FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- CORRECCIÓN: Añadimos 'jq' a la lista de instalación ---
RUN apt-get update && apt-get install -y curl ca-certificates unzip jq && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/ && \
    rm -rf /var/lib/apt/lists/*
# -----------------------------------------------------------

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY monitoring-scripts/ ./monitoring-scripts/

# Asegurar permisos de ejecución (que añadimos antes)
RUN chmod +x monitoring-scripts/*.sh

ENV PYTHONPATH=/app/src
ENV FLASK_PORT=5001
ENV FLASK_DEBUG=True

EXPOSE 5001

CMD ["python", "src/app.py"]