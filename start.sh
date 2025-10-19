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

# Start the server with daphne (ASGI) for WebSocket support
# Use PORT environment variable injected by Render
daphne -b 0.0.0.0 -p $PORT chat_api.asgi:application
