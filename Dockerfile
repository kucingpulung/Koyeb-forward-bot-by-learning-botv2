FROM python

# Update dan install git
RUN apt update && apt upgrade -y && apt install -y git

# Set environment variable untuk branch (opsional)
ENV BRANCH=""

# Copy requirements.txt untuk preinstall dependensi awal
COPY requirements.txt /requirements.txt

# Install Python dependensi (jika tersedia)
RUN pip3 install --upgrade pip && pip3 install -r /requirements.txt || true

# Salin start.sh dan beri permission eksekusi
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Jalankan script saat container start
CMD ["/bin/bash", "/start.sh"]
