FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalar dependencias base y kubectl
RUN apt-get update && apt-get install -y curl unzip && \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install flask

COPY app.py .

# No exponemos puerto aquí, se maneja en tiempo de ejecución, 
# pero es buena práctica documentarlo
EXPOSE 5001

CMD ["python", "app.py"]