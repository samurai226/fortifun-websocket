#!/bin/bash
# Start script for Django on Render

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Skip user seeding when accounts app is disabled
echo "Skipping user seeding - accounts app is disabled"

# Collect static files
python manage.py collectstatic --noinput

# Start the server with gunicorn (production)
# Use PORT environment variable injected by Render
gunicorn chat_api.wsgi:application --bind 0.0.0.0:$PORT --workers 3
