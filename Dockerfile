# Use official Python image optimized for Cloud Run
FROM python:3.12-slim

# Set environment variables for Cloud Run
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project and setup files
COPY adk_project ./adk_project
COPY setup.py .

# Install the project in editable mode
RUN pip install -e .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port for Cloud Run
EXPOSE 8080

# Health check optimized for Cloud Run
HEALTHCHECK --interval=60s --timeout=10s --start-period=10s --retries=2 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the API with uvicorn optimized for Cloud Run  
CMD ["sh", "-c", "uvicorn adk_project.api.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"] 