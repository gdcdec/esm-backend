#!/bin/sh -x

#sudo rm -rf api/migrations/* pgadmin_data/ postgres_data/
#touch api/migrations/__init__.py

MY_UID=`id -u` MY_GID=`id -g` docker compose up -d --build

#docker compose exec django python manage.py makemigrations api --merge
#docker compose exec django python manage.py migrate
