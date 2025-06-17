#!/bin/bash

cd /Ultra-Forward-Bot || exit 1

# Install dependencies (jaga-jaga)
pip3 install -U -r requirements.txt

echo "Starting Bot dan Webserver (Uptime Robot)..."
python3 main.py
