# Быстрый старт с OpenAPI

## Что такое OpenAPI?

OpenAPI (ранее Swagger) - это стандарт для описания REST API. Позволяет:
- Автоматически генерировать документацию
- Тестировать API через интерактивный интерфейс
- Создавать клиентские библиотеки
- Валидировать запросы и ответы

## Быстрый просмотр документации

### Онлайн (самый простой способ)

1. Откройте https://editor.swagger.io/
2. Скопируйте содержимое файла `openapi.yaml`
3. Вставьте в редактор
4. Готово! Вы видите интерактивную документацию

### Локально через Docker

```bash
# Запустите Swagger UI
docker run -p 8080:8080 \
  -e SWAGGER_JSON=/openapi.yaml \
  -v $(pwd)/openapi.yaml:/openapi.yaml \
  swaggerapi/swagger-ui

# Откройте http://localhost:8080
```

## Тестирование API

### Использование тестовых данных

Файл `test_data.json` содержит готовые примеры для всех endpoints.

### Пример: Регистрация и отправка сообщения

```bash
# 1. Регистрация
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "confirmPassword": "test123",
    "organization": "Тестовая компания"
  }'

# 2. Отправка сообщения
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Покажи баланс моих счетов",
    "history": [],
    "userData": {
      "email": "test@example.com",
      "organization": "Тестовая компания"
    },
    "files": []
  }'
```

## Основные endpoints

### Чат и AI
- `POST /api/chat/` - Отправка сообщения
- `GET /api/chat-status/{request_id}/` - Проверка статуса

### Пользователи
- `POST /api/register/` - Регистрация
- `POST /api/login/` - Авторизация
- `GET /api/user-data/` - Получение данных

### Метрики
- `GET /api/metrics/` - Получение метрик
- `GET /api/metrics/summary/` - Сводка метрик
- `POST /api/metrics/calculate/` - Расчет метрик

## Файлы

- `openapi.yaml` - OpenAPI спецификация
- `test_data.json` - Тестовые данные
- `OPENAPI.md` - Полная документация

## Дополнительная информация

Подробная документация: см. [OPENAPI.md](OPENAPI.md)

