# Диагностика проблем с подключением к LM Studio

## Быстрая проверка

### 1. Запустите скрипт диагностики

```bash
cd aichat
python check_lm_studio.py
```

Скрипт проверит:
- Доступность сервера LM Studio
- Доступность API endpoint
- Наличие и работоспособность модели

### 2. Проверьте через веб-интерфейс

Откройте в браузере:
```
http://localhost:8000/api/check-lm-studio/
```

Или используйте curl:
```bash
curl http://localhost:8000/api/check-lm-studio/
```

## Частые проблемы и решения

### Проблема: "Не удалось подключиться к серверу"

**Причины:**
1. LM Studio не запущен
2. Сервер не активен в LM Studio
3. Неправильный порт или URL

**Решение:**
1. Откройте LM Studio
2. Перейдите в раздел **Developer** (Разработчик)
3. Выберите модель `qwen3-vl-4b`
4. Нажмите **Server settings**
5. Включите **Serve on Local Network** (если нужно)
6. Убедитесь, что **Status: Running** (зеленый индикатор)
7. Проверьте, что порт **1234** указан правильно

### Проблема: "Модель не найдена"

**Причины:**
1. Модель не загружена
2. Неправильное имя модели
3. Модель не активна

**Решение:**
1. В LM Studio перейдите в раздел **Search**
2. Найдите и загрузите модель `qwen/qwen3-vl-4b`
3. В разделе **Developer** выберите загруженную модель
4. Убедитесь, что статус модели **READY**
5. Проверьте имя модели в `aichat/main/views.py` (строка 516) - должно быть `qwen3-vl-4b`

### Проблема: "Превышено время ожидания"

**Причины:**
1. Модель слишком медленная
2. Компьютер перегружен
3. Недостаточно оперативной памяти

**Решение:**
1. Используйте более легкую модель
2. Закройте другие приложения
3. Увеличьте таймаут в `aichat/main/views.py` (строка 522)

### Проблема: Порт 1234 занят

**Решение:**
1. Проверьте, какой процесс использует порт:
   ```bash
   # Windows
   netstat -ano | findstr :1234
   
   # Linux/Mac
   lsof -i :1234
   ```
2. Измените порт в LM Studio (Server Settings)
3. Обновите URL в `aichat/aichat/settings.py`:
   ```python
   LM_STUDIO_URL = 'http://localhost:НОВЫЙ_ПОРТ/v1/chat/completions'
   ```

## Проверка настроек

### URL в Django

Файл: `aichat/aichat/settings.py`
```python
LM_STUDIO_URL = 'http://localhost:1234/v1/chat/completions'
```

### Имя модели

Файл: `aichat/main/views.py` (строка 516)
```python
"model": "qwen3-vl-4b",  # Должно совпадать с именем в LM Studio
```

## Тестирование подключения вручную

### Через curl

```bash
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3-vl-4b",
    "messages": [{"role": "user", "content": "Привет"}],
    "max_tokens": 10
  }'
```

### Через Python

```python
import requests

response = requests.post(
    'http://localhost:1234/v1/chat/completions',
    json={
        "model": "qwen3-vl-4b",
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 10
    },
    timeout=10
)
print(response.status_code)
print(response.json())
```

## Дополнительная информация

- Официальный сайт LM Studio: https://lmstudio.ai/
- Документация API: https://lmstudio.ai/docs
- Если используете Docker, используйте `host.docker.internal` вместо `localhost`

