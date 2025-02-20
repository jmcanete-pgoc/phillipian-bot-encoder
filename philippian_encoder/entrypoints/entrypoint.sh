#!/bin/ash
python manage.py migrate
exec "$@"