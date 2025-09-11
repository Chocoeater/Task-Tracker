
# Task Tracker

Система управления задачами для команд: создание задач и подзадач, назначение исполнителей, отслеживание статусов. Поддерживает JWT-аутентификацию и роли пользователей (разработчик, менеджер, админ).

---

## Стек технологий

- Python 3.13  
- Django 5.x  
- Django REST Framework  
- PostgreSQL  
- Docker / Docker Compose  
- Poetry (управление зависимостями)  
- Simple JWT (аутентификация)  

---

## Установка и запуск локально (без Docker)

1. Клонируем репозиторий:

```bash
git clone https://github.com/Chocoeater/Task-Tracker.git
cd Task-Tracker
````

2. Устанавливаем Poetry (если ещё не установлен):

```bash
pip install poetry
```

3. Устанавливаем зависимости проекта через Poetry:

```bash
poetry install
```

4. Активируем виртуальное окружение Poetry:

```bash
poetry shell
```

5. Создаем `.env` файл в папке `back/` с содержимым (пример):

```env
DEBUG=True
SECRET_KEY=your_secret_key
DB_NAME=task_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=ваш_секретный_ключ
DEBUG=True
```

6. Применяем миграции:

```bash
python manage.py migrate
```

7. Создаем суперпользователя:

```bash
python manage.py create_admin
```

8. Запускаем сервер:

```bash
python manage.py runserver
```

---

## Запуск через Docker Compose (локально)

1. Убедитесь, что установлены Docker и Docker Compose.

2. Собираем и запускаем сервисы:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

> Сервис `back` — Django (с Poetry внутри), `db` — PostgreSQL.

3. Создаем суперпользователя в контейнере:

```bash
docker-compose -f docker-compose.dev.yml exec back python manage.py create_admin
```

5. Проект доступен на [http://localhost:8000](http://localhost:8000).

---

## Структура проекта

```
Task-Tracker/
├── back/                     # Django проект
│   ├── config/               # Приложения: tasks, users
│   ├── pyproject.toml        # Poetry конфигурация
│   ├── poetry.lock
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── Dockerfile.prod       # Продакшен
│   └── Dockerfile.dev        # Разработка
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── README.md
```

---

## Использование

* Создание нового пользователя исключительно правами админа
* JWT-аутентификация для всех запросов, кроме логина
* CRUD для задач и подзадач
* Фильтры и сортировка задач
* Роли пользователей: разработчик, менеджер, админ

---

## Полезные команды Docker

* Сборка и запуск:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

* Остановка контейнеров:

```bash
docker-compose -f docker-compose.dev.yml down
```

* Выполнение команд внутри контейнера Django:

```bash
docker-compose -f docker-compose.dev.yml exec back python manage.py <команда>
```

---

## Тесты

Запуск тестов через Poetry:

```bash
poetry run pytest
```

Запуск тестов внутри контейнера Docker:

```bash
docker-compose -f docker-compose.dev.yml exec back pytest
```

## Фикстуры

Для ручного тестирования добавлены фикстура с: 
- 1 админом

- 2 менеджерами

- 6 разработчиками

- 20 задачами (с подзадачами и зависимостями).

> Пароль у всех пользователей одинаковый: 12345678

Для локального запуска вне докера:

```bash
python manage.py loaddata initial_data.json
```

Для запуска в докере:

```bash
docker-compose -f docker-compose.dev.yml exec back python manage.py loaddata initial_data.json
```