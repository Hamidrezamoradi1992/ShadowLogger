#!/bin/sh

# Compile Persian translation files (fa) while ignoring 'env' directory
echo "Compile message translate"
python manage.py compilemessages --ignore=env -l fa

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate
python manage.py migrate --database=logs middleware
# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput


# Start the server or any other command passed as argument
echo "Starting server..."
gunicorn --bind 0.0.0.0:8008 core.wsgi





