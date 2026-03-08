FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY packages.txt ./

RUN apt-get update \
    && xargs -r -a packages.txt apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt install.sh ./

RUN chmod +x install.sh \
    && ./install.sh \
    && rm -rf /root/.cache/pip

COPY . .

EXPOSE 8080

CMD ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0"]
