#!/bin/bash
set -e

echo "============================================"
echo "  POSITIVE — Sovereign Intent Engine"
echo "============================================"

echo "[1/5] Running migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "[2/5] Compiling translations..."
python manage.py compilemessages --ignore=.venv 2>/dev/null || echo "  No translations to compile yet."

echo "[3/5] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "[4/5] Creating superuser if needed..."
python manage.py shell << 'PYEOF'
from django.contrib.auth.models import User
from core.models import UserProfile
if not User.objects.filter(username='admin').exists():
    u = User.objects.create_superuser('admin', 'admin@positive.local', 'positive2026')
    UserProfile.objects.get_or_create(u, defaults={'role': 'ARCHITECT'})
    print("  Created admin user: admin / positive2026")
    print("  IMPORTANT: Change this password at /admin after first login!")
else:
    print("  Admin user already exists.")
PYEOF

echo "[5/5] Starting server..."
exec gunicorn \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    positive_project.wsgi:application
