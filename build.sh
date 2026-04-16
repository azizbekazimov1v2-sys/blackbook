#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

echo "=== MIGRATE START ==="
python manage.py migrate

echo "=== COLLECT STATIC ==="
python manage.py collectstatic --noinput