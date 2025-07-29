#!/bin/sh
set -e

# Install full LaTeX using apt (Debian/Ubuntu)
echo "Updating package lists..."
apt-get update

echo "Installing full LaTeX distribution..."
apt-get install -y texlive-full

# Now your Python/Django and other setup

if [ ! -d "/media/static" ]; then
    mkdir -p /media/static
fi

cp -r /media_static_temp/* /media/static/ 2>/dev/null || true

python manage.py makemigrations api database discord discordoauth2 frontend script
python manage.py migrate
python manage.py makemigrations api database discord discordoauth2 frontend script
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py make-messages -a --ignore=project_root/*
django-admin compilemessages

gunicorn --bind 0.0.0.0:8000 core.wsgi:application & nginx -g 'daemon off;'
