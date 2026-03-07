FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests first to leverage Docker layer caching.
COPY requirements.txt install.sh ./

RUN chmod +x install.sh \
    && ./install.sh \
    && rm -rf /root/.cache/pip

# Copy the rest of the application after dependencies are installed.
COPY . .

EXPOSE 8501

CMD streamlit run main.py --server.port $PORT --server.address 0.0.0.0
