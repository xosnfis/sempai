# Документация по метрикам качества работы модели

## Обзор

Система метрик автоматически отслеживает и рассчитывает показатели качества работы AI-ассистента. Метрики собираются для каждого запроса и агрегируются за периоды времени.

## Модели данных

### Metric
Хранит агрегированные метрики за период времени:
- `name` - название метрики
- `category` - категория метрики
- `value` - значение метрики
- `target_value` - целевое значение
- `unit` - единица измерения (percent, seconds, requests_per_minute)
- `period_start`, `period_end` - период расчета
- `sample_size` - размер выборки

### ChatRequestMetrics
Хранит метрики для конкретного запроса:
- `processing_time` - время обработки запроса (секунды)
- `llm_processing_time` - время обработки LLM (секунды)
- `has_action` - есть ли действие в ответе
- `action_success` - успешно ли выполнено действие
- `files_processed`, `files_failed` - статистика обработки файлов
- `message_blocked`, `response_blocked` - блокировки модерации
- `context_used` - использован ли контекст пользователя

## API Endpoints

### GET /api/metrics/
Получение метрик за период.

**Параметры:**
- `days` (int, по умолчанию 7) - количество дней для расчета
- `category` (str, опционально) - фильтр по категории
- `metric` (str, опционально) - фильтр по названию метрики

**Пример запроса:**
```
GET /api/metrics/?days=30&category=performance
```

**Ответ:**
```json
{
  "success": true,
  "metrics": [
    {
      "name": "response_time_p50",
      "category": "performance",
      "value": 3.5,
      "target_value": 5.0,
      "unit": "seconds",
      "is_target_met": true,
      "sample_size": 150,
      "period_start": "2024-01-01T00:00:00Z",
      "period_end": "2024-01-31T23:59:59Z",
      "calculated_at": "2024-02-01T00:00:00Z",
      "metadata": {}
    }
  ],
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z",
    "days": 30
  },
  "total": 1
}
```

### POST /api/metrics/calculate/
Расчет метрик за указанный период.

**Тело запроса:**
```json
{
  "days": 7,
  "period_start": "2024-01-01T00:00:00Z",  // опционально
  "period_end": "2024-01-31T23:59:59Z"      // опционально
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Рассчитано 25 метрик",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "metrics_count": 25
}
```

### GET /api/metrics/summary/
Получение сводки метрик по категориям (для дашборда).

**Параметры:**
- `days` (int, по умолчанию 7) - количество дней

**Пример запроса:**
```
GET /api/metrics/summary/?days=7
```

**Ответ:**
```json
{
  "success": true,
  "summary": {
    "performance": {
      "name": "Производительность",
      "metrics": [
        {
          "name": "response_time_p50",
          "value": 3.5,
          "target_value": 5.0,
          "unit": "seconds",
          "is_target_met": true,
          "sample_size": 150
        }
      ]
    }
  },
  "statistics": {
    "total_requests": 200,
    "completed_requests": 190,
    "failed_requests": 10,
    "success_rate": 95.0
  },
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z",
    "days": 7
  }
}
```

## Категории метрик

### 1. response_quality (Качество ответов)
- `response_completeness` - полнота ответа (%)
- `business_style_compliance` - соответствие деловому стилю (%)

### 2. action_performance (Выполнение действий)
- `action_success_rate` - успешность выполнения действий (%)
- `command_recognition_rate` - распознавание команд (%)

### 3. performance (Производительность)
- `response_time_p50` - время ответа, медиана (секунды)
- `response_time_p95` - время ответа, 95-й перцентиль (секунды)
- `llm_processing_time_p50` - время обработки LLM, медиана (секунды)
- `throughput` - пропускная способность (запросов/минуту)

### 4. reliability (Надежность)
- `request_success_rate` - успешность обработки запросов (%)
- `error_rate` - частота ошибок (%)

### 5. security (Безопасность)
- `ai_response_blocking_rate` - частота блокировки ответов AI (%)
- `message_blocking_rate` - частота блокировки сообщений (%)

### 6. user_experience (Пользовательский опыт)
- `task_completion_rate` - процент завершенных задач (%)

### 7. file_processing (Обработка файлов)
- `file_processing_success_rate` - успешность обработки файлов (%)

### 8. data_accuracy (Точность данных)
- `context_utilization_rate` - использование контекста (%)

### 9. calendar (Работа с календарем)
- `event_creation_accuracy` - точность создания событий (%)
- `event_update_accuracy` - точность обновления событий (%)

### 11. user_engagement (Активность пользователей)
- `user_activity_rate` - среднее количество запросов на пользователя (запросов/пользователь)
  - Формула: `общее количество запросов / количество уникальных пользователей`
  - Показывает, насколько активно пользователи используют систему
  - Целевое значение: ≥ 5 запросов/пользователь
  
- `user_retention_rate_7d` - процент пользователей, вернувшихся через 7 дней (%)
  - Формула: `(пользователи, вернувшиеся через 7 дней / пользователи в базовом периоде) × 100%`
  - Показывает, сколько пользователей возвращаются к использованию системы
  - Целевое значение: ≥ 60%
  
- `user_retention_rate_30d` - процент пользователей, вернувшихся через 30 дней (%)
  - Формула: `(пользователи, вернувшиеся через 30 дней / пользователи в базовом периоде) × 100%`
  - Показывает долгосрочное удержание пользователей
  - Целевое значение: ≥ 40%

### 10. formatting (Форматирование)
- Метрики форматирования (можно расширить)

### 11. user_engagement (Активность пользователей)
- `user_activity_rate` - среднее количество запросов на пользователя (запросов/пользователь)
- `user_retention_rate_7d` - процент пользователей, вернувшихся через 7 дней (%)
- `user_retention_rate_30d` - процент пользователей, вернувшихся через 30 дней (%)

## Автоматический расчет метрик

Метрики автоматически рассчитываются при вызове `/api/metrics/summary/`, если за указанный период еще нет рассчитанных метрик.

Также можно настроить периодический расчет метрик через cron или Celery:

```python
from main.metrics_calculator import MetricsCalculator
from django.utils import timezone
from datetime import timedelta

# Расчет метрик за последние 7 дней
period_end = timezone.now()
period_start = period_end - timedelta(days=7)
MetricsCalculator.calculate_all_metrics(period_start, period_end)
```

## Целевые значения метрик

Целевые значения определены в `MetricsCalculator.TARGET_VALUES`:

- `response_relevance`: 85%
- `information_accuracy`: 90%
- `business_style_compliance`: 95%
- `response_completeness`: 80%
- `action_success_rate`: 90%
- `parameter_extraction_accuracy`: 85%
- `command_recognition_rate`: 95%
- `response_time_p50`: 5 секунд
- `response_time_p95`: 10 секунд
- `llm_processing_time_p50`: 3 секунды
- `throughput`: 10 запросов/минуту
- `request_success_rate`: 95%
- `error_rate`: ≤ 5%
- `content_moderation_effectiveness`: 98%
- `false_positive_rate`: ≤ 2%
- `ai_response_blocking_rate`: ≤ 1%
- `task_completion_rate`: 85%
- `clarification_rate`: ≤ 10%
- `file_processing_success_rate`: 90%
- `format_support_rate`: 95%
- `data_extraction_accuracy`: 90%
- `context_utilization_rate`: 80%
- `event_creation_accuracy`: 95%
- `event_update_accuracy`: 90%
- `table_formatting_accuracy`: 95%
- `chart_command_accuracy`: 90%
- `user_activity_rate`: 5 запросов/пользователь
- `user_retention_rate_7d`: 60%
- `user_retention_rate_30d`: 40%

## Просмотр метрик в админ-панели

Метрики доступны в Django Admin:
- `/admin/main/metric/` - список всех метрик
- `/admin/main/chatrequestmetrics/` - метрики конкретных запросов

## Применение миграций

После добавления новых моделей выполните:

```bash
python manage.py migrate
```

## Примеры использования

### Получение метрик производительности за месяц
```bash
curl "http://localhost:8000/api/metrics/?days=30&category=performance"
```

### Расчет метрик за последнюю неделю
```bash
curl -X POST "http://localhost:8000/api/metrics/calculate/" \
  -H "Content-Type: application/json" \
  -d '{"days": 7}'
```

### Получение сводки для дашборда
```bash
curl "http://localhost:8000/api/metrics/summary/?days=7"
```

## Расширение системы метрик

Для добавления новых метрик:

1. Добавьте расчет в соответствующий метод `MetricsCalculator` (например, `_calculate_formatting_metrics`)
2. Добавьте целевое значение в `TARGET_VALUES`
3. Метрика автоматически будет рассчитываться при вызове `calculate_all_metrics()`

