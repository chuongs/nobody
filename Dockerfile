FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency manifests first to leverage Docker layer caching.
COPY requirements.txt install.sh ./

RUN chmod +x install.sh \
    && ./install.sh \
    && rm -rf /root/.cache/pip

# Copy the rest of the application after dependencies are installed.
COPY . .

EXPOSE 8501

CMD ["sh", "-c", "streamlit run main.py --server.address=0.0.0.0 --server.port=${PORT:-8501}"]
