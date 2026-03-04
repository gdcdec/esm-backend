#!/bin/sh -x

rm -rf api/migrations/* pgadmin_data/ postgres_data/
touch api/migrations/__init__.py

docker compose up -d --build
docker compose exec django python manage.py makemigrations
docker compose exec django python manage.py migrate --fake
