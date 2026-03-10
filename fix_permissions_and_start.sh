#!/bin/bash

set -e  # Останавливаем при ошибке

echo "Подготовка окружения..."

# Исправляем права на postgres_data
if [ -d "postgres_data" ]; then
    echo "Исправление прав postgres_data..."
    # Удаляем старую директорию или меняем владельца на postgres (UID 999)
    # ВАЖНО: НЕ используем chmod 755, так как PostgreSQL требует владельца postgres
    sudo chown -R 999:999 postgres_data 2>/dev/null || sudo chown -R 999:999 postgres_data
    sudo chmod 700 postgres_data  # PostgreSQL требует 700 для безопасности
else
    mkdir -p postgres_data
    sudo chown 999:999 postgres_data
    chmod 700 postgres_data
fi
# Исправляем права на pgadmin4
sudo chown -R 5050:5050 pgadmin_data
sudo chmod -R 755 pgadmin_data
# Исправляем права на migrations
echo "Подготовка папки миграций..."
mkdir -p api/migrations
touch api/migrations/__init__.py  # Важно! Без этого файла Django не видит миграции
chmod -R 777 api/migrations 2>/dev/null || sudo chmod -R 777 api/migrations

# Проверяем наличие приложения api в INSTALLED_APPS
echo "Проверка конфигурации Django..."
if [ -f "api/config/settings.py" ]; then
    if ! grep -q "'api'" api/config/settings.py && ! grep -q "api.apps.ApiConfig" api/config/settings.py; then
        echo "Приложение 'api' не найдено в INSTALLED_APPS!"
        echo "Добавьте 'api' или 'api.apps.ApiConfig' в INSTALLED_APPS"
    fi
fi

# Останавливаем старые контейнеры
echo "Остановка старых контейнеров..."
docker compose down -v 2>/dev/null || docker compose down

# НЕ экспортируем MY_UID и MY_GID для PostgreSQL, так как это ломает права
# Вместо этого удаляем эти переменные из окружения
unset MY_UID
unset MY_GID

echo "Запуск контейнеров..."
docker compose up -d

# Ждем инициализации
echo "Ожидание запуска (30 секунд)..."
sleep 30

# Показываем логи
echo "Логи контейнеров (Ctrl+C для выхода):"
docker compose logs --tail=50 -f
