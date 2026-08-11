FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
COPY src/ ./src/
RUN pip install --no-cache-dir -r requirements.txt

# start gunicorn with uvicorn workers
EXPOSE 8000
ENV PYTHONPATH=/app/src
CMD ["gunicorn", "emtl_server.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "600", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
