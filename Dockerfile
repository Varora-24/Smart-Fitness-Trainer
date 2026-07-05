# ================================================================
#  Dockerfile  –  Dockerization for the AI Smart Fitness Trainer
# ================================================================

FROM python:3.11-slim-bookworm

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install OS system dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    portaudio19-dev \
    libportaudio2 \
    espeak \
    && (apt-get install -y --no-install-recommends libasound2t64 || apt-get install -y --no-install-recommends libasound2) \
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
CMD ["streamlit", "run", "Home.py", "--server.address=0.0.0.0"]
