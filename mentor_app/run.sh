#!/bin/bash
export FLASK_APP=app.py
export FLASK_ENV=production
gunicorn app:app -b 0.0.0.0:${PORT:-10000}
