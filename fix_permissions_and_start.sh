#!/bin/bash

set -e  # Останавливаем при ошибке

echo "Подготовка окружения..."

# Получаем текущий UID и GID пользователя
export MY_UID=$(id -u)
export MY_GID=$(id -g)

echo "Текущий пользователь: UID=$MY_UID, GID=$MY_GID"

# Исправляем права на postgres_data (меняем владельца на текущего пользователя, НО НЕ УДАЛЯЕМ)
if [ -d "postgres_data" ]; then
    echo "Исправление прав postgres_data для пользователя $MY_UID (данные сохраняются)..."
    # Меняем владельца рекурсивно, но не трогаем содержимое
    sudo chown -R $MY_UID:$MY_GID postgres_data
    # Убеждаемся, что права на директорию правильные
    sudo chmod 700 postgres_data
    echo "Права на postgres_data исправлены"
else
    echo "ОШИБКА: Директория postgres_data не существует!"
    exit 1
fi

# Исправляем права на pgadmin4 (pgadmin использует UID 5050, НО НЕ УДАЛЯЕМ)
if [ -d "pgadmin_data" ]; then
    echo "Исправление прав pgadmin_data (данные сохраняются)..."
    sudo chown -R 5050:5050 pgadmin_data
    sudo chmod -R 755 pgadmin_data
    echo "Права на pgadmin_data исправлены"
else
    echo "ОШИБКА: Директория pgadmin_data не существует!"
    exit 1
fi

# Исправляем права на migrations (от root)
echo "Исправление прав папки миграций..."
if [ -d "api/migrations" ]; then
    # Меняем права от root (777)
    sudo chmod -R 777 api/migrations
    echo "Права на api/migrations исправлены"
else
    echo "Создание папки миграций..."
    mkdir -p api/migrations
    touch api/migrations/__init__.py
    sudo chmod -R 777 api/migrations
fi

# Проверяем наличие приложения api в INSTALLED_APPS
echo "Проверка конфигурации Django..."
if [ -f "api/config/settings.py" ]; then
    if ! grep -q "'api'" api/config/settings.py && ! grep -q "api.apps.ApiConfig" api/config/settings.py; then
        echo "⚠️  Предупреждение: Приложение 'api' не найдено в INSTALLED_APPS!"
        echo "   Добавьте 'api' или 'api.apps.ApiConfig' в INSTALLED_APPS"
    else
        echo "✓ Приложение api найдено в INSTALLED_APPS"
    fi
fi

# Останавливаем старые контейнеры (с сохранением томов)
echo "Остановка старых контейнеров (тома сохраняются)..."
docker compose down  # БЕЗ флага -v, чтобы не удалять тома!

# Экспортируем UID/GID для Docker
export MY_UID
export MY_GID

# Пересобираем образы (если нужно)
echo "Пересборка образов Docker..."
docker compose build

# Запускаем контейнеры
echo "Запуск контейнеров с UID=$MY_UID, GID=$MY_GID..."
docker compose up -d

# Ждем инициализации
echo "Ожидание запуска (20 секунд)..."
sleep 20

# Проверяем статус
echo "Статус контейнеров:"
docker compose ps

# Проверяем логи PostgreSQL на наличие ошибок
echo "Проверка логов PostgreSQL:"
if docker compose logs postgres-db --tail=30 | grep -i error; then
    echo "❌ Найдены ошибки в PostgreSQL!"
    echo "Полные логи PostgreSQL:"
    docker compose logs postgres-db --tail=50
else
    echo "✓ Ошибок в PostgreSQL не найдено"
fi

# Проверяем логи Django
echo "Проверка логов Django:"
if docker compose logs django-app --tail=20 | grep -i error; then
    echo "⚠️  Найдены ошибки в Django"
else
    echo "✓ Django запустился без ошибок"
fi

echo "✅ Готово! Контейнеры запущены."
echo "📝 Для просмотра всех логов: docker compose logs -f"
echo "🔍 PostgreSQL данные сохранены в ./postgres_data"
echo "🔍 PgAdmin данные сохранены в ./pgadmin_data"
