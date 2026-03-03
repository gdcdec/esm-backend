#!/bin/bash
docker-compose down
sudo rm -rf api/migrations/
sudo mkdir -p api/migrations
sudo touch api/migrations/__init__.py
docker-compose down -v
docker-compose up -d
docker-compose exec django python manage.py makemigrations

if [ "$1" == "--fake" ]; then
    echo "Помечаем миграции как выполненные..."
    docker-compose exec django python manage.py migrate --fake
else
    echo "Применяем миграции реально..."
    docker-compose exec django python manage.py migrate
fi



if [ "$2" == "--admin" ]; then
    echo "Новая база, новый админ..."
    docker-compose exec django python manage.py createsuperuser
else
    echo "Старые данные есть..."
fi

