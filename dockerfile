FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=http \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py knowledge_base.md ./

# Run as a non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["python", "server.py"]