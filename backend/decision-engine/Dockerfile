FROM python:3.11-slim

WORKDIR /app

COPY common /app/common
RUN pip install --no-cache-dir -e /app/common

COPY backend/decision-engine/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/decision-engine/main.py /app/main.py

EXPOSE 8006

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8006"]
