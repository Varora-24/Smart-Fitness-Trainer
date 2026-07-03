# ================================================================
#  Dockerfile  –  Dockerization for the AI Smart Fitness Trainer
# ================================================================

FROM python:3.11-slim

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install OS system dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libasound2 \
    portaudio19-dev \
    libportaudio2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install pip requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copy all source files
COPY . .

# Expose Streamlit dashboard default port
EXPOSE 8501

# Default command runs the streamlit dashboard
CMD ["streamlit", "run", "dashboard.py", "--server.address=0.0.0.0"]
