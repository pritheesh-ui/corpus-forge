#!/usr/bin/env bash
set -e

if [ ! -d ".venv" ]; then
  if command -v python &> /dev/null; then
    python -m venv .venv
  else
    python3 -m venv .venv
  fi
fi

if [ -d ".venv/Scripts" ]; then
  source .venv/Scripts/activate
elif [ -d ".venv/bin" ]; then
  source .venv/bin/activate
else
  echo "Error: Virtual environment activation directory not found."
  exit 1
fi

python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env — add your GOOGLE_API_KEY before sending messages."
fi

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000