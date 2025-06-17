#!/bin/bash
# Install dependencies (jaga-jaga)
pip3 install -U -r requirements.txt

echo "Starting Bot dan Webserver (Uptime Robot)..."
python main.py
