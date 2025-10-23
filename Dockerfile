# RepoCloud Deploy için Dockerfile

FROM python:3.11-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Sistem paketlerini güncelle ve gerekli paketleri yükle
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python paketlerini yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyala
COPY repocloud_api_server.py .

# Port'u expose et
EXPOSE 8000

# Uygulamayı başlat
CMD ["uvicorn", "repocloud_api_server:app", "--host", "0.0.0.0", "--port", "8000"]
