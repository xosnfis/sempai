# OpenAPI спецификация для Альфа-Ассистент

## Описание

OpenAPI спецификация описывает все API endpoints проекта Альфа-Ассистент. Файл спецификации: `openapi.yaml`

## Файлы

- `openapi.yaml` - OpenAPI 3.0 спецификация со всеми endpoints
- `test_data.json` - Тестовые данные для использования с API

## Использование

### Просмотр документации

#### Вариант 1: Swagger UI (онлайн)

1. Откройте https://editor.swagger.io/
2. Скопируйте содержимое `openapi.yaml`
3. Вставьте в редактор
4. Просматривайте интерактивную документацию

#### Вариант 2: Swagger UI (локально)

```bash
# Установите Swagger UI через Docker
docker run -p 8080:8080 -e SWAGGER_JSON=/openapi.yaml -v $(pwd)/openapi.yaml:/openapi.yaml swaggerapi/swagger-ui

# Откройте в браузере
http://localhost:8080
```

#### Вариант 3: Redoc

```bash
# Установите Redoc через npm
npm install -g redoc-cli

# Запустите сервер документации
redoc-cli serve openapi.yaml

# Или сгенерируйте статический HTML
redoc-cli build openapi.yaml -o api-docs.html
```

### Генерация клиентских библиотек

#### Python клиент

```bash
# Установите openapi-generator
npm install -g @openapitools/openapi-generator-cli

# Сгенерируйте Python клиент
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o ./api-client/python
```

#### JavaScript/TypeScript клиент

```bash
# Сгенерируйте TypeScript клиент
openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o ./api-client/typescript
```

### Тестирование API

#### Использование тестовых данных

Файл `test_data.json` содержит готовые тестовые данные для всех endpoints:

```json
{
  "users": {
    "regular_user": {
      "email": "user@example.com",
      "password": "password123",
      "organization": "ООО Компания"
    }
  },
  "chat_requests": {
    "simple_message": {
      "message": "Покажи баланс моих счетов",
      ...
    }
  }
}
```

#### Пример использования с curl

```bash
# Регистрация пользователя
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "confirmPassword": "password123",
    "organization": "ООО Компания"
  }'

# Авторизация
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'

# Отправка сообщения в чат
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Покажи баланс моих счетов",
    "history": [],
    "userData": {
      "email": "user@example.com",
      "organization": "ООО Компания"
    },
    "files": []
  }'

# Получение метрик
curl "http://localhost:8000/api/metrics/?days=7&category=quality"
```

#### Пример использования с Python

```python
import requests
import json

# Загрузка тестовых данных
with open('test_data.json', 'r', encoding='utf-8') as f:
    test_data = json.load(f)

# Базовый URL
BASE_URL = "http://localhost:8000"

# Регистрация пользователя
register_data = {
    "email": test_data["users"]["regular_user"]["email"],
    "password": test_data["users"]["regular_user"]["password"],
    "confirmPassword": test_data["users"]["regular_user"]["password"],
    "organization": test_data["users"]["regular_user"]["organization"]
}

response = requests.post(f"{BASE_URL}/api/register/", json=register_data)
print(response.json())

# Авторизация
login_data = {
    "email": test_data["users"]["regular_user"]["email"],
    "password": test_data["users"]["regular_user"]["password"]
}

response = requests.post(f"{BASE_URL}/api/login/", json=login_data)
print(response.json())

# Отправка сообщения в чат
chat_data = test_data["chat_requests"]["simple_message"]
response = requests.post(f"{BASE_URL}/api/chat/", json=chat_data)
result = response.json()
print(result)

# Проверка статуса запроса
if result.get("success"):
    request_id = result["request_id"]
    status_response = requests.get(f"{BASE_URL}/api/chat-status/{request_id}/")
    print(status_response.json())

# Получение метрик
metrics_response = requests.get(f"{BASE_URL}/api/metrics/", params={"days": 7})
print(metrics_response.json())
```

#### Пример использования с JavaScript

```javascript
// Загрузка тестовых данных
const testData = require('./test_data.json');

const BASE_URL = 'http://localhost:8000';

// Регистрация пользователя
async function registerUser() {
  const response = await fetch(`${BASE_URL}/api/register/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: testData.users.regular_user.email,
      password: testData.users.regular_user.password,
      confirmPassword: testData.users.regular_user.password,
      organization: testData.users.regular_user.organization
    })
  });
  
  const data = await response.json();
  console.log(data);
  return data;
}

// Авторизация
async function login() {
  const response = await fetch(`${BASE_URL}/api/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: testData.users.regular_user.email,
      password: testData.users.regular_user.password
    })
  });
  
  const data = await response.json();
  console.log(data);
  return data;
}

// Отправка сообщения в чат
async function sendChatMessage() {
  const response = await fetch(`${BASE_URL}/api/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(testData.chat_requests.simple_message)
  });
  
  const data = await response.json();
  console.log(data);
  
  if (data.success) {
    // Проверка статуса
    const statusResponse = await fetch(`${BASE_URL}/api/chat-status/${data.request_id}/`);
    const statusData = await statusResponse.json();
    console.log(statusData);
  }
  
  return data;
}

// Получение метрик
async function getMetrics() {
  const response = await fetch(`${BASE_URL}/api/metrics/?days=7&category=quality`);
  const data = await response.json();
  console.log(data);
  return data;
}

// Использование
(async () => {
  await registerUser();
  await login();
  await sendChatMessage();
  await getMetrics();
})();
```

## Структура спецификации

### Основные разделы

1. **Чат AI** - endpoints для общения с AI-ассистентом
2. **Пользователи** - регистрация, авторизация, управление пользователями
3. **Календарь** - создание и управление событиями
4. **История чатов** - просмотр и экспорт истории
5. **Метрики** - получение метрик качества работы системы
6. **Утилиты** - вспомогательные endpoints

### Компоненты

- **Schemas** - схемы данных (ErrorResponse, Metric, Period)
- **Examples** - примеры запросов и ответов
- **Test Data** - тестовые данные в отдельном файле

## Обновление спецификации

При добавлении новых endpoints или изменении существующих:

1. Обновите `openapi.yaml`
2. Добавьте примеры в `test_data.json`
3. Обновите документацию в `README.md`

## Валидация спецификации

```bash
# Установите swagger-cli
npm install -g swagger-cli

# Валидация спецификации
swagger-cli validate openapi.yaml
```

## Интеграция с Django

Для автоматической генерации OpenAPI спецификации из Django можно использовать:

- `drf-yasg` - для Django REST Framework
- `django-rest-framework` - с встроенной поддержкой OpenAPI

## Полезные ссылки

- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger Editor](https://editor.swagger.io/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [Redoc](https://github.com/Redocly/redoc)

## Примеры использования

### Полный цикл работы с API

```python
import requests
import time
import json

BASE_URL = "http://localhost:8000"

# 1. Регистрация
register_response = requests.post(f"{BASE_URL}/api/register/", json={
    "email": "newuser@example.com",
    "password": "password123",
    "confirmPassword": "password123",
    "organization": "ООО Компания"
})
print("Регистрация:", register_response.json())

# 2. Авторизация
login_response = requests.post(f"{BASE_URL}/api/login/", json={
    "email": "newuser@example.com",
    "password": "password123"
})
print("Авторизация:", login_response.json())

# 3. Отправка сообщения
chat_response = requests.post(f"{BASE_URL}/api/chat/", json={
    "message": "Покажи баланс моих счетов",
    "history": [],
    "userData": {
        "email": "newuser@example.com",
        "organization": "ООО Компания"
    },
    "files": []
})
chat_result = chat_response.json()
print("Запрос отправлен:", chat_result)

# 4. Ожидание ответа
if chat_result.get("success"):
    request_id = chat_result["request_id"]
    
    # Проверяем статус каждые 2 секунды
    for i in range(30):  # Максимум 60 секунд
        time.sleep(2)
        status_response = requests.get(f"{BASE_URL}/api/chat-status/{request_id}/")
        status = status_response.json()
        print(f"Статус ({i+1}):", status.get("status"))
        
        if status.get("status") == "completed":
            print("Ответ:", status.get("response"))
            break
        elif status.get("status") == "failed":
            print("Ошибка:", status.get("error"))
            break

# 5. Получение метрик
metrics_response = requests.get(f"{BASE_URL}/api/metrics/summary/", params={"days": 7})
print("Метрики:", metrics_response.json())
```

## Поддержка

Если у вас возникли вопросы по использованию OpenAPI спецификации, обращайтесь:
- Email: support@alfa-assistant.ru
- Документация: см. `README.md`

