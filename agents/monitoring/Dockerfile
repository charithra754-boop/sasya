FROM python:3.11-slim

WORKDIR /app

COPY common /app/common
RUN pip install --no-cache-dir -e /app/common

COPY agents/monitoring/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/monitoring/main.py /app/main.py

EXPOSE 8014

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8014"]
