FROM python:3.10-slim

# Install required packages for PyQt5 + QWebEngine
RUN apt-get update && apt-get install -y \
    xvfb \
    libxkbcommon-x11-0 \
    libglu1-mesa \
    libnss3 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libxfixes3 \
    libxext6 \
    libxtst6 \
    libatk1.0-0 \
    libgtk-3-0 \
    libasound2 \
    libpci3 \
    libxss1 \
    libxshmfence1 \
    fonts-liberation \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]

newfile


FROM python:3.9-slim

# Install system dependencies for PyQt5 and Xvfb (for headless Qt)
RUN apt-get update && apt-get install -y \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libx11-xcb1 \
    libqt5gui5 \
    libqt5webkit5 \
    libqt5webengine5 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy application files
COPY requirements.txt .
COPY app.py .
COPY pdf_exporter.py .
COPY static/ static/
COPY templates/ templates/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DISPLAY=:99

# Start Xvfb and Flask
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 & flask run --host=0.0.0.0 --port=5000"]
