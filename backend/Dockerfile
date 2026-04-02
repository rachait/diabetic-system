FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend /workspace/backend
COPY app /workspace/app
COPY models /workspace/models
COPY data /workspace/data

WORKDIR /workspace/backend
EXPOSE 5000

CMD ["python", "run.py"]
