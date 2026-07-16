# --- Builder Stage ---
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment at /opt/venv
RUN python -m venv /opt/venv
# Ensure we use this venv for all subsequent pip installs
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /src
COPY requirements.txt .
# Install packages into the venv (no --user flag needed)
RUN pip install --no-cache-dir -r requirements.txt

# --- Runtime Stage ---
FROM python:3.13-slim
LABEL authors="cappe"

# Add the runtime user and group
RUN addgroup --system app && adduser --system --ingroup app app

# Install only runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsasl2-2 \
    libssl3 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the venv from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /src
# Copy application code
COPY ./src /src

# Set permissions for the app user so they can write/read the source and static files
RUN chown -R app:app /src

# Run collectstatic as the 'app' user to ensure permissions are correct
USER app

# Run build-time tasks
RUN SECRET_KEY=build-time-placeholder DEBUG=False python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["uvicorn", "pda.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "3"]