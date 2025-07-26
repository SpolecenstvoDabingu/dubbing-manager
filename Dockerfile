# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set environment variables for Django settings
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (e.g., SQLite)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sqlite3 \
    nginx \
    gettext \
    curl \
    unzip \
    texlive-latex-base \
    file \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy the requirements file to the container and install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Django project into the container
COPY ./dabing-manager /app/

# Expose the port the app will run on
EXPOSE 80

# Copy Nginx configuration file
COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /media/static

COPY ./static /media_static_temp/

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY maintenance.html /manager_static/maintenance.html

# Entry point to run migrations and start Django server with custom configurations
CMD ["/app/entrypoint.sh"]