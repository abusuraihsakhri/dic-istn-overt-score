FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir 'fastapi>=0.111,<1' 'uvicorn>=0.30,<1' 'pydantic>=2,<3'

COPY . .

# Default to the HTTP service; use python cli.py ... to run a scoring command.
CMD ["uvicorn", "agents.api:app", "--host", "0.0.0.0", "--port", "8000"]
