# Руководство по тестированию проекта Alfa

Этот документ содержит инструкции по запуску и использованию тестов для проекта Альфа-Ассистент.

## Обзор тестов

Проект включает **81 тест**, покрывающий следующие области:

-  **Модели данных** (14 тестов) - тестирование моделей ChatRequest и ChatHistory
-  **API Endpoints** (25 тестов) - тестирование всех API endpoints
-  **Модерация контента** (13 тестов) - тестирование системы модерации
-  **Обработка файлов** (11 тестов) - тестирование обработки различных форматов файлов
-  **Утилитарные функции** (10 тестов) - тестирование вспомогательных функций
-  **Интеграционные тесты** (3 теста) - тестирование взаимодействия компонентов
-  **Тесты безопасности** (4 теста) - тестирование защиты от уязвимостей
-  **Тесты производительности** (2 теста) - тестирование производительности

## Предварительные требования

### 1. Активировать виртуальное окружение

```powershell
# Перейти в директорию проекта
cd C:\Users\tasue\Desktop\alfa-finansi\sempaialfa-main\aichat

# Активировать виртуальное окружение
.\venv\Scripts\Activate.ps1

# Если возникает ошибка Execution Policy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### 2. Установить зависимости

```powershell
# Убедитесь, что все зависимости установлены
pip install -r ..\requirements.txt
```

### 3. Применить миграции

```powershell
# Применить миграции (если еще не применены)
python manage.py migrate
```

## Базовые команды для запуска тестов

### Запустить все тесты

```powershell
python manage.py test main.tests --verbosity=2
```

### Запустить все тесты с минимальным выводом

```powershell
python manage.py test main.tests --verbosity=1
```

### Запустить все тесты с максимальным выводом

```powershell
python manage.py test main.tests --verbosity=3
```

## Запуск тестов по категориям

### Тесты моделей

```powershell
# Все тесты моделей
python manage.py test main.tests.ChatRequestModelTest main.tests.ChatHistoryModelTest --verbosity=2

# Только ChatRequest
python manage.py test main.tests.ChatRequestModelTest --verbosity=2

# Только ChatHistory
python manage.py test main.tests.ChatHistoryModelTest --verbosity=2
```

### Тесты API

```powershell
# Все тесты API
python manage.py test main.tests.ChatAPITest main.tests.ChatStatusAPITest main.tests.ChatHistoryAPITest main.tests.CalendarEventAPITest main.tests.CheckLMStudioAPITest main.tests.UserDataAPITest --verbosity=2

# Только тесты чата
python manage.py test main.tests.ChatAPITest --verbosity=2

# Только тесты статуса
python manage.py test main.tests.ChatStatusAPITest --verbosity=2

# Только тесты истории
python manage.py test main.tests.ChatHistoryAPITest --verbosity=2

# Только тесты календаря
python manage.py test main.tests.CalendarEventAPITest --verbosity=2
```

### Тесты модерации контента

```powershell
python manage.py test main.tests.ContentModeratorTest --verbosity=2
```

### Тесты обработки файлов

```powershell
python manage.py test main.tests.FileProcessorTest --verbosity=2
```

### Тесты утилитарных функций

```powershell
python manage.py test main.tests.UtilityFunctionsTest --verbosity=2
```

### Интеграционные тесты

```powershell
python manage.py test main.tests.IntegrationTest --verbosity=2
```

### Тесты безопасности

```powershell
python manage.py test main.tests.SecurityTest --verbosity=2
```

### Тесты производительности

```powershell
python manage.py test main.tests.PerformanceTest --verbosity=2
```

## Запуск конкретных тестов

### Запустить один конкретный тест

```powershell
python manage.py test main.tests.ChatRequestModelTest.test_create_chat_request --verbosity=2
```

### Запустить несколько конкретных тестов

```powershell
python manage.py test main.tests.ChatRequestModelTest.test_create_chat_request main.tests.ChatRequestModelTest.test_chat_request_default_status --verbosity=2
```

## Полезные флаги

### Сохранить тестовую базу данных между запусками

```powershell
python manage.py test main.tests --keepdb --verbosity=2
```

Это ускорит последующие запуски тестов, так как база данных не будет пересоздаваться.

### Остановиться на первой ошибке

```powershell
python manage.py test main.tests --failfast --verbosity=2
```

### Запустить тесты в параллельном режиме

```powershell
python manage.py test main.tests --parallel --verbosity=2
```

## Проверка покрытия кода тестами

### Установка coverage

```powershell
pip install coverage
```

### Запуск тестов с измерением покрытия

```powershell
# Запуск тестов с coverage
coverage run --source='.' manage.py test main.tests

# Просмотр отчета в консоли
coverage report

# Генерация HTML отчета
coverage html

# Открыть HTML отчет (в браузере)
# Файл будет в папке htmlcov/index.html
```

### Просмотр покрытия конкретного модуля

```powershell
coverage report --include="main/*"
```

## Решение проблем при тестировании

### Проблема: "ModuleNotFoundError"

**Решение:**
```powershell
# Убедитесь, что виртуальное окружение активно
# Должно быть (venv) в начале строки PowerShell

# Установите зависимости
pip install -r ..\requirements.txt
```

### Проблема: "Database errors" или "table already exists"

**Решение:**
```powershell
# Удалить базу данных и применить миграции заново
Remove-Item db.sqlite3 -ErrorAction SilentlyContinue
python manage.py migrate
python manage.py test main.tests --verbosity=2
```

### Проблема: "database table is locked"

**Примечание:** Это не критичная ошибка. Она возникает из-за асинхронных потоков в фоновой обработке запросов. Тесты все равно проходят успешно (ok), просто в логах есть предупреждения из фоновых потоков.

Если хотите избежать этих предупреждений, можно временно отключить асинхронную обработку в тестах.

### Проблема: Тесты выполняются медленно

**Решение:**
```powershell
# Используйте флаг --keepdb для сохранения тестовой БД
python manage.py test main.tests --keepdb --verbosity=1

# Или запускайте только нужные тесты
python manage.py test main.tests.ChatRequestModelTest --verbosity=1
```

## Структура тестов

Тесты организованы в следующие классы:

1. **ChatRequestModelTest** - тесты модели ChatRequest
2. **ChatHistoryModelTest** - тесты модели ChatHistory
3. **ContentModeratorTest** - тесты модерации контента
4. **FileProcessorTest** - тесты обработки файлов
5. **UtilityFunctionsTest** - тесты утилитарных функций
6. **ChatAPITest** - тесты API чата
7. **ChatStatusAPITest** - тесты API статуса
8. **ChatHistoryAPITest** - тесты API истории
9. **CalendarEventAPITest** - тесты API календаря
10. **CheckLMStudioAPITest** - тесты проверки подключения
11. **UserDataAPITest** - тесты API данных пользователя
12. **IntegrationTest** - интеграционные тесты
13. **SecurityTest** - тесты безопасности
14. **PerformanceTest** - тесты производительности

## Примеры успешного выполнения

При успешном выполнении всех тестов вы увидите:

```
Found 81 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
........... (81 точек или названий тестов)
----------------------------------------------------------------------
Ran 81 tests in X.XXXs

OK
Destroying test database for alias 'default'...
```

## Добавление новых тестов

При добавлении новых тестов:

1. Добавьте тест в соответствующий класс в `main/tests.py`
2. Запустите тест для проверки:
   ```powershell
   python manage.py test main.tests.ВашКлассТестов.ваш_тест --verbosity=2
   ```
3. Убедитесь, что все тесты проходят:
   ```powershell
   python manage.py test main.tests --verbosity=2
   ```

## Автоматизация тестов

### Запуск тестов перед коммитом (Git hooks)

Создайте файл `.git/hooks/pre-commit`:

```bash
#!/bin/sh
cd sempaialfa-main/aichat
python manage.py test main.tests --verbosity=1
```

### Запуск тестов в CI/CD

Пример для GitHub Actions:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          cd sempaialfa-main
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd sempaialfa-main/aichat
          python manage.py test main.tests --verbosity=2
```

## Контакты

Если у Вас возникли вопросы по тестированию, обращайтесь к команде Семпаи.

