FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variables for Gunicorn and Flask
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
# PORT environment variable is typically set by Cloud Run
ENV PORT 8080

# Command to run the application using Gunicorn
# Use the PORT environment variable Cloud Run provides.
CMD exec gunicorn --bind :$PORT --workers 2 --threads 2 --timeout 0 app:app

