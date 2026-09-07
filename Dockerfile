FROM python:3.11-slim

WORKDIR /app

# Suppress pip root user warnings in Docker
ENV PIP_ROOT_USER_ACTION=ignore
# Memory-conserving mode for cloud free tier containers (<= 512MB RAM)
ENV ENABLE_VIT_MODEL=false

# Install system dependencies for OpenCV and networking
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-cache lightweight insightface model during image build to prevent request timeouts
RUN python -c "from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_s', providers=['CPUExecutionProvider']).prepare(ctx_id=0)"

COPY . .

EXPOSE 8000

CMD ["python", "app.py", "--serve", "--host", "0.0.0.0"]
