FROM python:3.11-slim

WORKDIR /app

# Install libpcap for Scapy
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpcap0.8 \
    && rm -rf /var/lib/apt/lists/*

# Reuse the same requirements if possible, or create a specific one
# For now, we assume capture/requirements.txt exists with scapy and httpx
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
