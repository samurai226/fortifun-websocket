#!/bin/bash
# Start script for Django on Render

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed sample users if none exist
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
from django.db import connection
try:
    # Ensure table exists before querying
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1 FROM accounts_user LIMIT 1;')
    if User.objects.count() == 0:
        print('Seeding sample users...')
        import subprocess, sys
        subprocess.run([sys.executable, 'manage.py', 'seed_users'], check=False)
    else:
        print('Users already present, skipping seed.')
except Exception as e:
    print(f'Skip seeding (table not ready or error): {e}')
"

# Create test user if it doesn't exist
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='testuser@example.com').exists():
    User.objects.create_user('testuser', 'testuser@example.com', 'TestPass123!')
    print('Test user created')
else:
    print('Test user already exists')
"

# Collect static files
python manage.py collectstatic --noinput

# Start the server with gunicorn (production)
gunicorn chat_api.wsgi:application --bind 0.0.0.0:8000 --workers 3
