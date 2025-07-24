#!/bin/sh
set -e

if [ ! -d "/media/static" ]; then
    mkdir -p /media/static
fi

cp -r /media_static_temp/* /media/static/ 2>/dev/null || true

python manage.py makemigrations api database discord discordoauth2 frontend
python manage.py migrate
python manage.py makemigrations api database discord discordoauth2 frontend
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py make-messages -a
django-admin compilemessages

gunicorn --bind 0.0.0.0:8000 core.wsgi:application & nginx -g 'daemon off;'