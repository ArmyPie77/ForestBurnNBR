FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for rasterio/GDAL
RUN apt-get update && \
    apt-get install -y --no-install-recommends gdal-bin libgdal-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000

# Use shell form so $PORT is expanded by the shell (Render sets PORT)
CMD ["/bin/sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-5000} --timeout 600 api_server:app"]
