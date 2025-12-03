# Быстрый старт: Работа с метриками в PowerShell

## Проблема: Скрипт не запускается

Если вы видите ошибку:
```
.\get-metrics.ps1: Имя ".\get-metrics.ps1" не распознано...
```

### Решение 1: Использовать полный путь

```powershell
# Из директории alfa
.\sempaialfa-main\get-metrics.ps1 -Action summary -Days 7

# Или из директории sempaialfa-main
cd sempaialfa-main
.\get-metrics.ps1 -Action summary -Days 7
```

### Решение 2: Использовать скрипт из корневой директории

Скрипт теперь также находится в `C:\Users\tasue\Desktop\alfa\get-metrics.ps1`

```powershell
# Из директории alfa
.\get-metrics.ps1 -Action summary -Days 7
```

### Решение 3: Если ошибка политики выполнения

Если видите ошибку:
```
не может быть загружен, так как выполнение сценариев отключено в этой системе
```

Выполните:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Затем попробуйте снова:
```powershell
.\get-metrics.ps1 -Action summary -Days 7
```

## Примеры использования

### 1. Получить сводку метрик за 7 дней
```powershell
.\get-metrics.ps1 -Action summary -Days 7
```

### 2. Рассчитать метрики за 30 дней
```powershell
.\get-metrics.ps1 -Action calculate -Days 30
```

### 3. Получить метрики активности пользователей
```powershell
.\get-metrics.ps1 -Action get -Days 30 -Category user_engagement
```

### 4. Получить конкретную метрику
```powershell
.\get-metrics.ps1 -Action get -Days 30 -Metric user_activity_rate
```

## Альтернатива: Использовать команды напрямую

Если скрипт не работает, используйте команды напрямую:

```powershell
# Сводка метрик
Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/summary/?days=7" | ConvertTo-Json -Depth 10

# Расчет метрик
$body = @{ days = 30 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/calculate/" `
    -Method POST -ContentType "application/json" -Body $body | ConvertTo-Json

# Метрики активности
Invoke-RestMethod -Uri "http://localhost:8000/api/metrics/?days=30&category=user_engagement" | ConvertTo-Json -Depth 10
```

## Проверка расположения скрипта

```powershell
# Проверить, где находится скрипт
Get-ChildItem -Path . -Filter "get-metrics.ps1" -Recurse

# Или
Get-ChildItem -Path C:\Users\tasue\Desktop\alfa -Filter "get-metrics.ps1" -Recurse
```

