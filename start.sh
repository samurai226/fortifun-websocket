#!/bin/bash
# Start script for Django on Render

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

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

# Start the server
python manage.py runserver 0.0.0.0:8000
