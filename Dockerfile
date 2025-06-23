# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project root to /app
COPY . /app

# Set PYTHONPATH so Python can find adk_project as a package
ENV PYTHONPATH="/app"

# Expose the port FastAPI will run on
EXPOSE 8080

# Start FastAPI app with uvicorn using full module path
CMD ["uvicorn", "adk_project.api.main:app", "--host", "0.0.0.0", "--port", "8080"] 