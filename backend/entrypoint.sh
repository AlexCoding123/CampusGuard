#!/bin/bash
set -e

# Start camera_opener in the background
echo "Starting camera_opener..."
python -m camera_opener &
CAMERA_PID=$!

# Start FastAPI main.py
echo "Starting FastAPI main.py..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
