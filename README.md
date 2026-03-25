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

Запустить shell-скрипт:

```bash
./run_compose.sh
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
| POST | `/posts/<id>/` | Служебный POST по посту (см. ниже про `doc`) |
| PATCH | `/posts/<id>/` | Обновить пост |
| DELETE | `/posts/<id>/` | Удалить пост |
| GET | `/users/<user_id>/posts/` | Посты пользователя |

**Поля поста:** `title`, `description`, `address`, `latitude`, `longitude`, `status` (draft/published/archived).

---

**Фильтры для списков постов (`/posts/` и частично `/users/<user_id>/posts/`):**

- `?rubric=<name>` — фильтр по рубрике (по имени рубрики).
- `?city=<строка>` — город/населённый пункт (подстрока в `address`, например `?city=Самара`).
- `?state=<строка>` — область/регион (подстрока в `address`, например `?state=Самарская`).
- `?address=<строка>` — общая подстрока в `address` (улица, часть адреса и т.п.).
- `?house_number=<строка>` — номер дома (также ищется как подстрока в `address`).
- `?author_id=<id>` — фильтр по автору (только для `/posts/`).
- `?date_start=YYYY-MM-DD` / `?date_end=YYYY-MM-DD` — фильтр по периоду публикации (для `/posts/`).
- Для `/users/<user_id>/posts/` доступны: `rubric`, `address`, а также `status` (для своих постов).

**Служебный GET по посту (`/posts/<id>/?doc=1`):**

- **Запрос**:
  - `GET /api/posts/<id>/?doc=1`
- **Ответ**:
  - При `doc == "1"` →  
    ```json
    {
      "letter": "<сгенерированный текст обращения>",
      "message": "Сгенерирован текст универсального обращения. Скопируйте и вставьте в нужную форму."
    }
    ```
  - Доступ к генерации письма: только автор поста (и требуется авторизация по токену).
  
Текст обращения формируется на основе данных пользователя (ФИО, адрес проживания, контакты) и поста (рубрика как тема нарушения, адрес события, дата/время, описание, количество фото) и подходит для копирования в формы ведомств/писем.

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
Ответ: `{address, latitude, longitude, city, street, house}` — работает для любых координат.

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
| `NOMINATIM_USER_AGENT` | User-Agent для Nominatim |
| `NOMINATIM_REFERER` | Referer для Nominatim |
| `DB_*` | PostgreSQL (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT) |

---

## Postman

В папке `postman/` лежат коллекции для тестирования API. Импортируйте их в Postman и создайте Environment с `base_url = http://localhost:8000/api`.

См. `postman/README.md` для деталей.
