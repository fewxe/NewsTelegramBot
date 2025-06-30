FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
COPY src ./src
COPY main.py .
COPY .env .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "main.py"]
