FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .
# Use local Basher (no pip install); /app is in PYTHONPATH when running from here
# RUN pip3 install --break-system-packages --no-cache-dir -e .

ENTRYPOINT ["python3", "install-oro.py"]
CMD ["--no-interaction"]
