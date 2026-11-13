#!/bin/bash
VENV_PATH="./venv/bin/activate"

echo "Activating virtual environment..."
source "$VENV_PATH"

echo "Starting FastAPI server..."
uvicorn app:app --host 0.0.0.0 --port 8007
