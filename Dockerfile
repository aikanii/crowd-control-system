FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create models dir and try to download (optional, will fallback to HOG if fails)
RUN mkdir -p models && \
    wget -q https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/MobileNetSSD_deploy.prototxt -O models/MobileNetSSD_deploy.prototxt || true

EXPOSE 5000

CMD ["python", "main.py", "--web", "--web-host", "0.0.0.0", "--web-port", "5000", "--no-display"]
