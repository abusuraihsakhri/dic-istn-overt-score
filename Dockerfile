FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set a default AUDIT_SECRET_KEY for container (override in production)
ENV AUDIT_SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir pydantic pytest

COPY . .

# Default command runs the CLI in overt mode with example values
# Override with: docker run dic-istn-overt-score python cli.py <command>
CMD ["python", "cli.py", "overt", "--platelets", "80", "--fibrin-marker", "moderate_increase", "--pt-prolongation", "4", "--fibrinogen", "1.5"]
