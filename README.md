# ESM Backend — EcoSignalMap / Сознательный гражданин

Django REST API для проекта «Сознательный гражданин» — приложения для сообщений об инцидентах с геолокацией и фотографиями.

## Стек

- **Python 3.12** · Django · Django REST Framework · PostgreSQL · Pillow · Nominatim (OpenStreetMap)

## Запуск

### Локально

```bash
pip install -r requirements.txt
cp .env.example .env   # настроить переменные
python manage.py migrate
python manage.py runserver
```

### Docker

```bash
docker-compose up -d --build
docker exec -it django-app python manage.py migrate
```

API: `http://localhost:8000/api/`

---

## API

Базовый URL: `http://localhost:8000/api/`

Авторизация: заголовок `Authorization: Token <auth_token>` (кроме эндпоинтов AllowAny).

---

### Аутентификация

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/auth/register/` | Регистрация |
| POST | `/auth/login/` | Вход (username/email + password) |
| POST | `/auth/logout/` | Выход (удаление токена) |
| POST | `/auth/password-reset/request/` | Запрос кода сброса (email) |
| POST | `/auth/password-reset/verify/` | Проверка кода (email, code) |
| POST | `/auth/password-reset/confirm/` | Установка нового пароля |

**Register** — body: `{"username","email","password","password2","first_name","last_name",...}`  
**Login** — body: `{"username":"user@email.com","password":"..."}` → ответ: `{"token","user_id",...}`

---

### Посты / сообщения

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/posts/` | Список постов (авторизованные видят свои черновики) |
| POST | `/posts/` | Создать пост |
| GET | `/posts/<id>/` | Детали поста |
| PATCH | `/posts/<id>/` | Обновить пост |
| DELETE | `/posts/<id>/` | Удалить пост |
| GET | `/users/<user_id>/posts/` | Посты пользователя |

**Поля поста:** `title`, `description`, `address`, `latitude`, `longitude`, `status` (draft/published/archived).

---

### Фотографии

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/posts/photos/upload/` | Загрузить фото (form-data: `post_id`, `photos[]`) |
| DELETE | `/posts/photos/<id>/` | Удалить фото |

---

### Адреса (Nominatim / карты)

Интеграция с OpenStreetMap для геокодирования. Публичный доступ (без токена).

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/address/reverse/` | Координаты → адрес |
| GET | `/address/search/?q=...&limit=5` | Поиск по адресу |

**Reverse** — body: `{"lat": 53.225664, "lon": 50.194162}`  
Ответ: `{in_working_area, address, latitude, longitude, city, street, house}`  
При `in_working_area: false` возвращается сообщение «В данном районе проект пока не работает».

---

### Рубрики

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/rubrics/` | Список рубрик |
| POST | `/rubrics/` | Создать рубрику |
| GET/PUT/PATCH/DELETE | `/rubrics/<name>/` | CRUD по имени |

---

## Настройки (settings / .env)

| Переменная | Описание |
|------------|----------|
| `PROJECT_WORKING_AREAS` | Города/области проекта (через запятую), напр. `Самара,Самарская область` |
| `NOMINATIM_USER_AGENT` | User-Agent для Nominatim |
| `NOMINATIM_REFERER` | Referer для Nominatim |
| `DB_*` | PostgreSQL (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT) |

---

## Postman

В папке `postman/` лежат коллекции для тестирования API. Импортируйте их в Postman и создайте Environment с `base_url = http://localhost:8000/api`.

См. `postman/README.md` для деталей.
