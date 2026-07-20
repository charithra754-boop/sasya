FROM python:3.11-slim

WORKDIR /app

COPY common /app/common
RUN pip install --no-cache-dir -e /app/common

COPY backend/auth-service/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/auth-service/main.py /app/main.py

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
