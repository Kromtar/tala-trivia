FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .
EXPOSE 8000

ENV PYTHONPATH=/app

# Dado el contexto del proyecto no se ha considerado una rutina de inicio en modo producción
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]