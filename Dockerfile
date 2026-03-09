FROM python:3.12-slim

# Аргументы для UID и GID (можно передать при сборке)
ARG UID=1000
ARG GID=1000

# Создаем группу и пользователя с указанными UID/GID
RUN groupadd -g ${GID} appuser && \
    useradd -m -u ${UID} -g appuser appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Устанавливаем зависимости для psycopg2 и Pillow (от root)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем Python-зависимости (от root)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Меняем владельца всех файлов на appuser
RUN chown -R appuser:appuser /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Команда по умолчанию (будет переопределена в docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
