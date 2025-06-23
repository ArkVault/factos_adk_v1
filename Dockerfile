# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the entire project into the container
COPY . /app

# Install any needed packages specified in requirements.txt
# The '-e .' will install our adk_project as a package
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV GOOGLE_CLOUD_PROJECT=factos-adk-agents

# New command to run the FastAPI app with uvicorn
CMD ["uvicorn", "adk_project.api.main:app", "--host", "0.0.0.0", "--port", "8080"] 