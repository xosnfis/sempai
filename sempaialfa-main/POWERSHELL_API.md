# Работа с API через PowerShell

## Проблема с curl в PowerShell

В PowerShell команда `curl` является алиасом для `Invoke-WebRequest`, который использует другой синтаксис, чем стандартный `curl`. Поэтому команды вида `curl -X POST ...` не работают.

## Решения

### Вариант 1: Использовать Invoke-RestMethod (рекомендуется)

`Invoke-RestMethod` автоматически парсит JSON ответы:

```powershell
# GET запрос
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/summary/?days=7" -Method GET
$response | ConvertTo-Json -Depth 10

# POST запрос
$body = @{
    days = 30
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/calculate/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$response | ConvertTo-Json -Depth 10
```

### Вариант 2: Использовать Invoke-WebRequest

```powershell
# GET запрос
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/metrics/summary/?days=7" -Method GET
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10

# POST запрос
$body = '{"days": 30}'
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/metrics/calculate/" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Вариант 3: Использовать curl.exe напрямую

Если у вас установлен curl.exe (Windows 10+), можно использовать его напрямую:

```powershell
curl.exe -X POST http://localhost:8000/api/metrics/calculate/ `
    -H "Content-Type: application/json" `
    -d "{\"days\": 30}"
```

### Вариант 4: Использовать готовый скрипт

Используйте скрипт `get-metrics.ps1`:

```powershell
# Сводка метрик за 7 дней
.\get-metrics.ps1 -Action summary -Days 7

# Расчет метрик за 30 дней
.\get-metrics.ps1 -Action calculate -Days 30

# Получение метрик активности пользователей
.\get-metrics.ps1 -Action get -Days 30 -Category user_engagement

# Получение конкретной метрики
.\get-metrics.ps1 -Action get -Days 30 -Metric user_activity_rate
```

## Примеры команд для метрик

### 1. Получить сводку метрик

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/summary/?days=7" | ConvertTo-Json -Depth 10
```

### 2. Рассчитать метрики

```powershell
$body = @{ days = 30 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/calculate/" `
    -Method POST -ContentType "application/json" -Body $body | ConvertTo-Json
```

### 3. Получить метрики активности пользователей

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/?days=30&category=user_engagement" | ConvertTo-Json -Depth 10
```

### 4. Получить конкретную метрику

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/?days=30&metric=user_activity_rate" | ConvertTo-Json -Depth 10
```

## Полезные функции PowerShell

### Сохранение результата в файл

```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/summary/?days=30"
$response | ConvertTo-Json -Depth 10 | Out-File -FilePath "metrics.json" -Encoding UTF8
```

### Фильтрация результатов

```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/?days=30&category=user_engagement"
$response.metrics | Where-Object { $_.name -eq "user_activity_rate" } | ConvertTo-Json
```

### Форматирование таблицы

```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/?days=30&category=user_engagement"
$response.metrics | Select-Object name, value, target_value, unit | Format-Table
```

## Сравнение синтаксиса

| curl (Linux/Mac) | PowerShell (Invoke-RestMethod) |
|------------------|-------------------------------|
| `curl -X GET URL` | `Invoke-RestMethod -Uri URL -Method GET` |
| `curl -X POST URL -H "Content-Type: application/json" -d '{"key":"value"}'` | `Invoke-RestMethod -Uri URL -Method POST -ContentType "application/json" -Body '{"key":"value"}'` |
| `curl URL?param=value` | `Invoke-RestMethod -Uri "URL?param=value"` |

## Решение проблем

### Ошибка: "Не удается найти параметр -X"
**Причина**: PowerShell интерпретирует `curl` как `Invoke-WebRequest`  
**Решение**: Используйте `Invoke-RestMethod` или `curl.exe`

### Ошибка: "Имя не распознано"
**Причина**: Многострочные команды в PowerShell требуют обратных кавычек  
**Решение**: Используйте обратные кавычки `` ` `` для переноса строк или одну строку

### Ошибка: "Cannot bind parameter"
**Причина**: Неправильный синтаксис параметров  
**Решение**: Используйте правильный синтаксис PowerShell (см. примеры выше)

