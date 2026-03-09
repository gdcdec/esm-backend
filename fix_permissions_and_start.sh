#!/bin/bash

set -e  # Останавливаем при ошибке

echo "🔧 Подготовка окружения..."

# Исправляем права на postgres_data
if [ -d "postgres_data" ]; then
    echo "Исправление прав postgres_data..."
    sudo chmod -R 755 postgres_data 2>/dev/null || true
else
    mkdir -p postgres_data
fi

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
docker compose down

# Запускаем с текущим пользователем
export MY_UID=$(id -u)
export MY_GID=$(id -g)

echo "Запуск с UID=$MY_UID, GID=$MY_GID"
docker compose up -d

# Ждем инициализации
echo "Ожидание запуска..."
sleep 5

# Показываем логи
echo "Логи контейнеров:"
docker compose logs --tail=50 -f
