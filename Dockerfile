# Dockerfile for TravelBuddy backend application
FROM python:3.12-slim

# Set environment variables and working directory
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1
WORKDIR /app

# Install dependencies and copy application code
COPY requirements.txt .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into the container
COPY app/ ./app/

# Copy individual Python files into the container
COPY db.py server.py ./

# Expose the application port and define the default command to run the server
EXPOSE 5001

# Run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "server:create_app()"]