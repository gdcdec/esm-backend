#!/bin/sh
#
# Description:
#     Creates a new administrative account(s)
#
# Directory structure:
#     esm-backend/.admins/
#     |-- admins.txt
#     |-- user01.txt
#     |-- ...
#     `-- user10.txt
#
# The './admins' directory must exist and consist of the 'admins.txt' file
# containing the list of users separated by whitespace characters (spaces,
# tabs or line feeds) and *.txt files named accordingly to the 'admins.txt'
# file. For example, say 'admins.txt' has the following content:
#
#     bob
#     dumb
#
# then the '.admins/' directory must contain 'bob.txt' and 'dumb.txt' files.
#
# Format of a 'user.txt' file:
#     email <email> 
#     password <password>
#
# The file 'user.txt' must consist of the two lines. Each line has two fields.
# The right field should be filled by the actual content and separated from
# the left field by a SINGLE (it's important) space char.

USERS_DIR=.admins
USERS_FILE=${USERS_DIR}/admins.txt
USERS=`cat ${USERS_DIR}/${USER_FILE}`

if [ ! "$USERS" ]; then
    echo "WARN: At least one user should be specified in the \"$USERS_FILE\""
    exit 0
fi

for I in $USERS; do
    USER_FILE=${USERS_DIR}/${I}.txt

    if [ ! -f $USER_FILE ]; then
        echo "WARN: File $USER_FILE doesn't exist"
        continue
    fi

    USERNAME=$I
    EMAIL=`grep email $USER_FILE | cut -f 2 -d ' '`
    PASSWORD=`grep password $USER_FILE | cut -f 2 -d ' '`

    echo Creating \"$I\" admin account...
    docker compose exec \
        -e DJANGO_SUPERUSER_USERNAME="$USERNAME" \
        -e DJANGO_SUPERUSER_EMAIL="$EMAIL" \
        -e DJANGO_SUPERUSER_PASSWORD="$PASSWORD" \
        django python manage.py createsuperuser --noinput
done
