FROM python:3.11-slim

WORKDIR /app


RUN pip install --no-cache-dir kafka-python==2.0.1

RUN pip install --no-cache-dir aiokafka==0.7.2

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
