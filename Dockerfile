FROM ghcr.io/astral-sh/uv:latest AS uv_bin
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app/src

# Copiar binario de uv
COPY --from=uv_bin /uv /uvx /bin/

# Dependencias del sistema para OpenCV GUI y soporte X11
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias del proyecto usando uv
COPY pyproject.toml uv.lock* ./
RUN uv pip install --system -r pyproject.toml

# Copiar código fuente
COPY src ./src
COPY main.py .

# Script por defecto
CMD ["python3", "-m", "clasificador.main"]