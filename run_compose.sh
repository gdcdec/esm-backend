#!/bin/sh -x

rm -rf api/migrations/* pgadmin_data/ postgres_data/

docker compose up -d --build
docker compose exec django python manage.py makemigrations api
