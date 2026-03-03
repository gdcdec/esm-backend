#!/bin/sh -x

docker ps --filter status=running \
    | grep -E -q "postgres|pgadmin4|django"

# Shutdown containers if they already up
if [ $? -eq 0 ]; then
    docker compose down
fi

rm -rf api/migrations/
mkdir -p api/migrations
touch api/migrations/__init__.py

# Check for necessary docker images
docker image ls --format "{{.Repository}}" --quiet \
    | grep -E -q "postgres|pgadmin4|django"

if [ $? -eq 0 ]; then
    docker compose up -d
else
    # Build the images if they haven't created yet
    docker compose up -d --build
fi

docker compose exec django python manage.py makemigrations api

#docker compose exec django python manage.py migrate
#docker compose exec django python manage.py 
