FROM python:3.10.11-slim

WORKDIR /app

COPY . /app

RUN chmod +x install.sh
RUN ./install.sh

EXPOSE 8501

CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
