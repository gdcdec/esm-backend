#!/bin/sh
#
# Description:
#     Creates a new administrative account
#
# Directory structure:
#     .esm-backend/.users/
#     |-- user01.txt
#     |-- ...
#     `-- user10.txt
#
# The '.users/' directory must consist of the 'users.txt' file, the list of
# users separated by whitespace characters (spaces, tabs or line feeds),
# and *.txt files named accordingly to the 'users.txt' file. For example,
# if 'users.txt' has the following content:
#
#     bob
#     dumb
#
# then the '.users/' directory must contain 'bob.txt' and 'dumb.txt' files.
#
# Format of a 'userX.txt' file:
#     email <email> 
#     password <password>
#
# The file 'userX.txt' consists of the two lines. Each line has two
# fields. The right field should be filled by the actual content
# and separated from the left field by a SINGLE (a single, it's important)
# space char.

USERS_DIR=.users
USERS=`cat ${USERS_DIR}/users.txt`

for I in $USERS; do
    USER_FILE=${USERS_DIR}/${I}.txt

    if [ ! -f $USER_FILE ]; then
        echo "WARN: File $USER_FILE doesn't exist"
        continue
    fi

    USERNAME=$I
    EMAIL=`grep email $USER_FILE | cut -f 2 -d ' '`
    PASSWORD=`grep password $USER_FILE | cut -f 2 -d ' '`

    docker compose exec \
        -e DJANGO_SUPERUSER_USERNAME="$USERNAME" \
        -e DJANGO_SUPERUSER_EMAIL="$EMAIL" \
        -e DJANGO_SUPERUSER_PASSWORD="$PASSWORD" \
        django python manage.py createsuperuser --noinput
done
