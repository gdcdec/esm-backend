#!/usr/bin/env python
import os
import time
import sys
import psycopg2
from psycopg2 import OperationalError

def wait_for_db():
    db_host = os.environ.get('DB_HOST', 'postgres-db')
    db_name = os.environ.get('DB_NAME', 'postgres')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'mysecretpassword')
    db_port = os.environ.get('DB_PORT', '5432')
    
    max_attempts = 30
    attempt = 1
    
    print(f"Подключение к {db_host}:{db_port}...")
    
    while attempt <= max_attempts:
        try:
            print(f"Попытка {attempt}/{max_attempts}...")
            conn = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password,
                port=db_port,
                connect_timeout=3
            )
            conn.close()
            print("✅ Успешное подключение к PostgreSQL!")
            return True
        except OperationalError as e:
            print(f"❌ Ошибка: {e}")
            attempt += 1
            time.sleep(2)
    
    print("❌ Не удалось подключиться к PostgreSQL")
    sys.exit(1)

if __name__ == "__main__":
    wait_for_db()
