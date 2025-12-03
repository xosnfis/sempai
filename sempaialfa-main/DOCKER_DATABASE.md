# Настройка базы данных PostgreSQL в Docker

## Обзор

Проект настроен для работы с PostgreSQL в Docker контейнере. Это обеспечивает:
- Надежность и масштабируемость
- Изоляцию данных
- Автоматические бэкапы через volumes
- Простое управление через Docker Compose

## Быстрый старт

### 1. Запуск с PostgreSQL (рекомендуется)

```bash
# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps

# Просмотреть логи
docker-compose logs -f web
docker-compose logs -f db
```

### 2. Применение миграций

Миграции применяются автоматически при запуске. Если нужно применить вручную:

```bash
docker-compose exec web python manage.py migrate
```

### 3. Создание суперпользователя

```bash
docker-compose exec web python manage.py createsuperuser
```

### 4. Доступ к админ-панели

Откройте в браузере: `http://localhost:8000/admin/`

## Настройка через переменные окружения

### Вариант 1: Использование .env файла (рекомендуется)

1. Создайте файл `.env` в корне проекта:

```env
# База данных
DB_ENGINE=django.db.backends.postgresql
DB_NAME=alfa_db
DB_USER=alfa_user
DB_PASSWORD=your_secure_password_here
DB_HOST=db
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

2. Docker Compose автоматически загрузит переменные из `.env`

### Вариант 2: Переменные в docker-compose.yml

Переменные уже настроены в `docker-compose.yml` с значениями по умолчанию.

## Подключение к базе данных

### Из контейнера Django

```bash
docker-compose exec web python manage.py dbshell
```

### Извне Docker (если порт открыт)

```bash
# Установите PostgreSQL клиент (если еще не установлен)
# Windows: скачайте с postgresql.org
# Linux: sudo apt-get install postgresql-client
# macOS: brew install postgresql

psql -h localhost -p 5432 -U alfa_user -d alfa_db
```

### Через Docker контейнер

```bash
docker-compose exec db psql -U alfa_user -d alfa_db
```

## Управление данными

### Создание бэкапа

```bash
docker-compose exec db pg_dump -U alfa_user alfa_db > backup.sql
```

### Восстановление из бэкапа

```bash
docker-compose exec -T db psql -U alfa_user alfa_db < backup.sql
```

### Очистка базы данных

```bash
# Остановить контейнеры
docker-compose down

# Удалить volume с данными
docker volume rm sempaialfa-main_postgres_data

# Запустить заново
docker-compose up -d
```

## Переключение между SQLite и PostgreSQL

### Использование PostgreSQL (Docker)

```bash
docker-compose up -d
```

### Использование SQLite (локально)

1. Остановите Docker контейнеры:
```bash
docker-compose down
```

2. Убедитесь, что переменные окружения не установлены или установите:
```bash
export DB_ENGINE=django.db.backends.sqlite3
```

3. Запустите локально:
```bash
python manage.py migrate
python manage.py runserver
```

## Мониторинг базы данных

### Просмотр размера базы данных

```bash
docker-compose exec db psql -U alfa_user -d alfa_db -c "SELECT pg_size_pretty(pg_database_size('alfa_db'));"
```

### Просмотр активных подключений

```bash
docker-compose exec db psql -U alfa_user -d alfa_db -c "SELECT * FROM pg_stat_activity;"
```

### Просмотр таблиц

```bash
docker-compose exec db psql -U alfa_user -d alfa_db -c "\dt"
```

## Решение проблем

### Ошибка подключения к базе данных

1. Проверьте, что контейнер БД запущен:
```bash
docker-compose ps
```

2. Проверьте логи:
```bash
docker-compose logs db
```

3. Проверьте health check:
```bash
docker-compose exec db pg_isready -U alfa_user
```

### Ошибка "database does not exist"

База данных создается автоматически при первом запуске. Если ошибка сохраняется:

```bash
docker-compose exec db createdb -U alfa_user alfa_db
```

### Миграции не применяются

Примените вручную:

```bash
docker-compose exec web python manage.py migrate
```

### Проблемы с правами доступа

Проверьте переменные окружения:
```bash
docker-compose exec web env | grep DB_
```

## Production настройки

Для production рекомендуется:

1. **Использовать сильные пароли** в `.env` файле
2. **Отключить DEBUG**: `DEBUG=False`
3. **Настроить ALLOWED_HOSTS**: `ALLOWED_HOSTS=yourdomain.com`
4. **Использовать SSL** для подключения к БД
5. **Настроить регулярные бэкапы**
6. **Ограничить доступ к порту БД** (не открывать наружу)

Пример production `.env`:

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=alfa_db_prod
DB_USER=alfa_user_prod
DB_PASSWORD=very_secure_password_here
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## Полезные команды

```bash
# Перезапуск всех сервисов
docker-compose restart

# Перезапуск только базы данных
docker-compose restart db

# Просмотр использования ресурсов
docker stats

# Очистка неиспользуемых ресурсов
docker system prune -a
```

## Структура volumes

Данные PostgreSQL хранятся в Docker volume `postgres_data`, который:
- Сохраняется при перезапуске контейнеров
- Может быть экспортирован для бэкапа
- Изолирован от других контейнеров

Просмотр volumes:
```bash
docker volume ls
docker volume inspect sempaialfa-main_postgres_data
```

