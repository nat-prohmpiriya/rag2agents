#!/bin/bash
# Start backend development server with hot reload

set -e

cd "$(dirname "$0")/../backend"

# Use absolute path to venv Python to ensure correct environment
export PATH="$(pwd)/.venv/bin:$PATH"

echo "Starting FastAPI development server..."
.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
