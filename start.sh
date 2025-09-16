#!/bin/bash
# Start script for Django on Render

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser if it doesn't exist
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@forti.com').exists():
    User.objects.create_superuser('admin', 'admin@forti.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Start the server
python manage.py runserver 0.0.0.0:8000
