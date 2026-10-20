#!/usr/bin/env bash
# Render's build command for the web service (see ../render.yaml).
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
