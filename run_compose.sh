#!/bin/sh

# Take uid and gid of the current user
MY_UID=`id -u`
MY_GID=`id -g`

POSTGRES_DIR=postgres_data
PGADMIN_DIR=pgadmin_data
MIGRATIONS_DIR=api/migrations

if [ -d $POSTGRES_DIR ]; then
    sudo chown -R $MY_UID:$MY_GID $POSTGRES_DIR
    sudo chmod 770 $POSTGRES_DIR
else
    mkdir $POSTGRES_DIR
fi

if [ -d $PGADMIN_DIR ]; then
    sudo chown -R 5050:5050 $PGADMIN_DIR
    sudo chmod -R 755 $PGADMIN_DIR
else
    mkdir $PGADMIN_DIR
fi

if [ -d $MIGRATIONS_DIR ]; then
    sudo chmod -R 777 $MIGRATIONS_DIR
else
    mkdir -p $MIGRATIONS_DIR
    touch ${MIGRATIONS_DIR}/__init__.py
    sudo chmod -R 777 $MIGRATIONS_DIR
fi

MY_UID=$MY_UID MY_GID=$MY_GID docker compose up -d --build

echo "Wait..."
sleep 10
