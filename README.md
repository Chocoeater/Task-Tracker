
# Task Tracker

Система управления задачами для команд: создание задач и подзадач, назначение исполнителей, отслеживание статусов. Поддерживает JWT-аутентификацию и роли пользователей (разработчик, менеджер, админ).

---

Автор: Коурдаков Илья

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
git checkout develop
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

5. Создаем `.env` файл в корне проекта с содержимым (пример):

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
docker-compose -f docker-compose.dev.yml up -d --build
```

> Сервис `back` — Django (с Poetry внутри), `db` — PostgreSQL.

3. Создаем суперпользователя в контейнере:

```bash
docker-compose -f docker-compose.dev.yml exec back python manage.py create_admin
```

5. Проект доступен на [http://localhost:8000](http://localhost:8000).

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
python manage.py test
```

Запуск тестов внутри контейнера Docker:

```bash
docker-compose -f docker-compose.dev.yml exec back python manage.py test
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
python manage.py loaddata fixtures/initial_data.json
```

Для удаления наполнения БД:
```bash
python manage.py flush
```

Для запуска в докере:

```bash
docker-compose -f docker-compose.dev.yml exec back python manage.py loaddata fixtures/initial_data.json
```

И для удаления:

```bash
docker-compose -f docker-compose.dev.yml exec back python manage.py flush
```

---

## Основной функционал

### 1. Задачи (`Task`)
Каждая задача содержит:

- `title` краткое название  
- `description` подробное описание  
- `author` создатель  
- `executor` исполнитель  
- `status` состояние задачи  
- `priority` приоритет (low/medium/high)  
- `deadline` крайний срок  
- `completed_at` когда задача была завершена  
- `parent` ссылка на родительскую задачу (поддержка вложенности)
- `created_at`, `updated_at` системные отметки

### 2. Поддерживаемые статусы

`todo` задача создана, но не взята в работу
`in_progress` в работе
`done` выполнена
`archived` перенесена в архив

При переходе задачи в статус **done**, если `completed_at` ещё пустой — заполняется автоматически текущей датой/временем.

### 3. Иерархия задач

Любая задача может иметь подзадачи:
```
Создать дизайн
└── Подготовить макеты
└── Собрать правки от команды
```
Это удобно для сложных задач или группировки небольших активностей.


### 4. Валидации

Модель защищает данные:

- нельзя назначить дедлайн раньше текущего времени  
- завершённая задача должна иметь статус `done`  
- при `done` автоматически проставляется `completed_at`  
- нельзя быть автором и исполнителем одновременно (если такое ограничение включено в проект)  
- подзадача не может ссылаться сама на себя  

---

## 🧬 Примеры работы API

### Создание задачи

```http
POST /api/tasks/
{
  "title": "Сверстать страницу профиля",
  "description": "Адаптив: desktop + mobile",
  "executor": 3,
  "priority": "high",
  "deadline": "2025-12-31 18:00"
}
```
### Изменение статуса
```http
PATCH /api/tasks/12/
{
  "status": "in_progress"
}
```
### Завершение задачи
```http
PATCH /api/tasks/12/
{
  "status": "done"
}
```
После этого:
```json
"completed_at": "2025-10-13T15:42:11Z"
```
ставится автоматически.

### Получение своих задач
```http
GET /api/tasks/my/
```
### Получение подзадач
```http
GET /api/tasks/5/subtasks/
```

---


## Структура проекта
```
Task_Tracker/
├── tasks/               # Основная логика задач
│   ├── models.py        # Модель Task + бизнес-логика
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
├── users/               # Пользователи и авторизация
│   ├── models.py
│   ├── serializers.py
│   └── views.py
├── config/              # Django настройки
├── nginx/               # Прокси-сервер для продакшена
└── docker-compose.yml   # Полностью докеризированный запуск
```

---

## Авторизация
Используется:

- JWT (SimpleJWT)

- собственная модель пользователя

- система ролей (admin, user)

- доступ к задачам по авторству и назначением исполнителя

