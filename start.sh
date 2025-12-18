#!/bin/bash
# Startup script that handles PORT environment variable

PORT=${PORT:-8000}
uvicorn api:app --host 0.0.0.0 --port $PORT
