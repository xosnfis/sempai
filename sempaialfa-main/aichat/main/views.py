from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import time
import json
import re
import requests
import base64
import logging
from datetime import datetime
from django.conf import settings
from .file_processor import process_file

logger = logging.getLogger(__name__)


def index(request):
    """Главная страница"""
    # Добавляем timestamp для обхода кеша
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/index.html', context)


def cabinet(request):
    """Страница личного кабинета"""
    # Добавляем timestamp для обхода кеша
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/cabinet.html', context)


def chat(request):
    """Страница чата"""
    # Добавляем timestamp для обхода кеша
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/chat.html', context)


def transfer(request):
    """Страница перевода средств"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/transfer.html', context)


def receipts(request):
    """Страница чеков"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/receipts.html', context)


def utilities(request):
    """Страница коммунальных услуг"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/utilities.html', context)


def taxes(request):
    """Страница налоговых выплат"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/taxes.html', context)


def calendar(request):
    """Страница календаря"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/calendar.html', context)


def documents(request):
    """Страница документов"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/documents.html', context)


def inventory(request):
    """Страница инвентаризации"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/inventory.html', context)


def employees(request):
    """Страница сотрудников"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/employees.html', context)


def support(request):
    """Страница поддержки"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/support.html', context)


def mail(request):
    """Страница почты"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/mail.html', context)


def login(request):
    """Страница входа/регистрации"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/login.html', context)


def feedback(request):
    """Страница обратной связи"""
    context = {
        'cache_version': int(time.time())
    }
    return render(request, 'main/feedback.html', context)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def check_lm_studio_connection(request):
    """API endpoint для проверки подключения к LM Studio"""
    try:
        LM_STUDIO_URL = getattr(settings, 'LM_STUDIO_URL', 'http://host.docker.internal:1234/v1/chat/completions')
        
        # Проверяем доступность базового URL
        base_url = LM_STUDIO_URL.rsplit('/v1/', 1)[0]
        
        try:
            # Проверка 1: Доступность сервера
            server_response = requests.get(base_url, timeout=5)
            server_available = True
        except:
            server_available = False
        
        # Проверка 2: Доступность API с тестовым запросом
        api_available = False
        model_available = False
        error_details = None
        
        if server_available:
            try:
                test_payload = {
                    "model": "qwen3-vl-4b",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                }
                api_response = requests.post(LM_STUDIO_URL, json=test_payload, timeout=10)
                
                if api_response.status_code == 200:
                    api_available = True
                    model_available = True
                elif api_response.status_code == 404:
                    api_available = True
                    model_available = False
                    error_details = "Модель 'qwen3-vl-4b' не найдена"
                else:
                    api_available = True
                    try:
                        error_data = api_response.json()
                        error_details = f"Статус {api_response.status_code}: {error_data}"
                    except:
                        error_details = f"Статус {api_response.status_code}"
            except requests.exceptions.ConnectionError:
                api_available = False
                error_details = "Не удалось подключиться к API endpoint"
            except requests.exceptions.Timeout:
                api_available = False
                error_details = "Превышено время ожидания"
            except Exception as e:
                api_available = False
                error_details = str(e)
        
        return JsonResponse({
            'success': server_available and api_available and model_available,
            'server_available': server_available,
            'api_available': api_available,
            'model_available': model_available,
            'url': LM_STUDIO_URL,
            'error': error_details,
            'recommendations': [] if (server_available and api_available and model_available) else [
                'Убедитесь, что LM Studio запущен',
                'Проверьте, что сервер активен (Status: Running в разделе Developer)',
                'Проверьте, что модель qwen3-vl-4b загружена и активна',
                'Проверьте, что порт 1234 не занят другим приложением',
                'Проверьте настройки сервера в LM Studio (Server Settings)'
            ]
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка проверки: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def get_user_data(request):
    """API endpoint для получения данных пользователя"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '')
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email не указан'
            }, status=400)
        
        # Здесь мы возвращаем структуру данных, которые должны быть в localStorage
        # Фактически данные будут переданы из фронтенда
        return JsonResponse({
            'success': True,
            'message': 'Данные должны быть переданы из фронтенда'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_calendar_event(request):
    """API endpoint для создания события в календаре"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '')
        title = data.get('title', '')
        date = data.get('date', '')
        description = data.get('description', '')
        
        if not all([email, title, date]):
            return JsonResponse({
                'success': False,
                'error': 'Не все обязательные поля заполнены'
            }, status=400)
        
        # Возвращаем данные для сохранения в localStorage на фронтенде
        event = {
            'id': str(int(time.time() * 1000)),
            'title': title,
            'date': date,
            'description': description,
            'notified': False
        }
        
        return JsonResponse({
            'success': True,
            'event': event
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка: {str(e)}'
        }, status=500)


def format_user_context(user_data):
    """Форматирует данные пользователя для передачи в AI"""
    context_parts = []
    
    # Балансы счетов
    balance1 = user_data.get('accountBalance', 0)
    balance2 = user_data.get('accountBalance2', 0)
    if balance1 or balance2:
        context_parts.append(f"Балансы счетов: Счет 1 - {balance1:,.0f} ₽, Счет 2 - {balance2:,.0f} ₽")
    
    # Чеки
    receipts = user_data.get('receipts', [])
    if receipts:
        total_receipts = len(receipts)
        total_amount = sum(r.get('amount', 0) for r in receipts if isinstance(r.get('amount'), (int, float)))
        context_parts.append(f"\nЧЕКИ: всего {total_receipts} операций на сумму {total_amount:,.0f} ₽")
        if receipts:
            recent = receipts[-5:]  # Последние 5 чеков (сокращено для экономии токенов)
            context_parts.append("Последние операции:")
            for r in recent:
                op_type = r.get('operationType', 'Операция')
                amount = r.get('amount', 0)
                date = r.get('date', '')
                desc = r.get('description', '')
                context_parts.append(f"  - {op_type}: {amount:,.0f} ₽ ({date}) {desc}")
    
    # Инвентаризация
    inventory = user_data.get('inventory', [])
    if inventory:
        context_parts.append(f"\nИНВЕНТАРИЗАЦИЯ: {len(inventory)} позиций")
        categories = {}
        for item in inventory:
            # Поддерживаем оба варианта: folder и folderId
            cat = item.get('folder') or item.get('folderId') or 'Без категории'
            categories[cat] = categories.get(cat, 0) + 1
        if categories:
            context_parts.append("Категории: " + ", ".join([f"{k}: {v} шт." for k, v in categories.items()]))
        # Детали по позициям
        context_parts.append("Позиции:")
        total_inventory_value = 0
        for item in inventory[:5]:  # Первые 5 позиций (сокращено для экономии токенов)
            name = item.get('name', 'Без названия')
            quantity = item.get('quantity', 0)
            price = item.get('price', 0)
            # Поддерживаем оба варианта: folder и folderId
            folder = item.get('folder') or item.get('folderId') or 'Без категории'
            total_cost = quantity * price if isinstance(price, (int, float)) and isinstance(quantity, (int, float)) else 0
            total_inventory_value += total_cost
            if price > 0:
                context_parts.append(f"  - {name}: {quantity} шт. × {price:,.2f} ₽ = {total_cost:,.2f} ₽ (категория: {folder})")
            else:
                context_parts.append(f"  - {name}: {quantity} шт. (категория: {folder}, стоимость не указана)")
        
        # Общая стоимость инвентаризации
        if total_inventory_value > 0:
            # Считаем общую стоимость всех позиций
            all_items_value = sum(
                item.get('quantity', 0) * item.get('price', 0) 
                for item in inventory 
                if isinstance(item.get('quantity'), (int, float)) and isinstance(item.get('price'), (int, float))
            )
            context_parts.append(f"Общая стоимость инвентаризации: {all_items_value:,.2f} ₽")
    
    # Сотрудники
    employees = user_data.get('employees', [])
    if employees:
        total_salary = sum(e.get('salary', 0) for e in employees if isinstance(e.get('salary'), (int, float)))
        context_parts.append(f"\nСОТРУДНИКИ: {len(employees)} человек, общий фонд зарплат {total_salary:,.0f} ₽")
        context_parts.append("Список сотрудников:")
        for emp in employees:
            fio = emp.get('fio', 'Не указано')
            salary = emp.get('salary', 0)
            position = emp.get('position', 'Не указана')
            context_parts.append(f"  - {fio} ({position}): {salary:,.0f} ₽")
    
    # Календарь
    calendar_events = user_data.get('calendarEvents', [])
    if calendar_events:
        context_parts.append(f"\nКАЛЕНДАРЬ: {len(calendar_events)} событий")
        upcoming = [e for e in calendar_events if e.get('date')]
        upcoming.sort(key=lambda x: x.get('date', ''))
        upcoming = upcoming[:5]  # Ближайшие 5 событий (сокращено для экономии токенов)
        if upcoming:
            context_parts.append("Ближайшие события (для обновления используй UPDATE_EVENT с ID или названием):")
            for e in upcoming:
                event_id = e.get('id', '')
                title = e.get('title', 'Событие')
                date = e.get('date', '')
                desc = e.get('description', '')
                # Извлекаем ISO формат даты (YYYY-MM-DDTHH:mm)
                iso_date = ''
                if date:
                    try:
                        event_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        iso_date = event_date.strftime('%Y-%m-%dT%H:%M')
                    except:
                        if 'T' in date:
                            iso_date = date[:16]  # Берем первые 16 символов (YYYY-MM-DDTHH:mm)
                        else:
                            iso_date = date
                context_parts.append(f"  - ID: {event_id} | Название: '{title}' | Дата ISO: {iso_date} | Описание: {desc}")
    
    # Налоги
    taxes_data = user_data.get('taxesData', {})
    if taxes_data:
        context_parts.append(f"\nНАЛОГИ:")
        tax_names = {
            'profit': 'Налог на прибыль',
            'vat': 'НДС',
            'property': 'Налог на имущество',
            'insurance': 'Страховые взносы'
        }
        total_tax_debt = 0
        for tax_id, tax_data in taxes_data.items():
            debt = tax_data.get('debt', 0)
            if isinstance(debt, (int, float)) and debt > 0:
                tax_name = tax_names.get(tax_id, tax_id)
                context_parts.append(f"  - {tax_name}: {debt:,.0f} ₽")
                total_tax_debt += debt
        if total_tax_debt > 0:
            context_parts.append(f"Общая задолженность по налогам: {total_tax_debt:,.0f} ₽")
    
    # Коммунальные услуги
    utilities_data = user_data.get('utilitiesData', {})
    if utilities_data:
        context_parts.append(f"\nКОММУНАЛЬНЫЕ УСЛУГИ:")
        util_names = {
            'electricity': 'Электричество',
            'water': 'Водоснабжение',
            'heating': 'Отопление',
            'waste': 'Вывоз ТКО',
            'security': 'Охранные услуги',
            'internet': 'Интернет'
        }
        total_utilities_debt = 0
        for util_id, util_data in utilities_data.items():
            debt = util_data.get('debt', 0)
            if isinstance(debt, (int, float)) and debt > 0:
                util_name = util_names.get(util_id, util_id)
                context_parts.append(f"  - {util_name}: {debt:,.0f} ₽")
                total_utilities_debt += debt
        if total_utilities_debt > 0:
            context_parts.append(f"Общая задолженность по коммунальным услугам: {total_utilities_debt:,.0f} ₽")
    
    # Документы
    documents = user_data.get('documents', [])
    if documents:
        context_parts.append(f"\nДОКУМЕНТЫ: {len(documents)} файлов")
        for doc in documents[:3]:  # Первые 3 документа (сокращено для экономии токенов)
            name = doc.get('name', 'Без названия')
            size = doc.get('size', 0)
            doc_type = doc.get('type', 'неизвестный тип')
            context_parts.append(f"  - {name} ({doc_type}, {size} байт)")
            # Не добавляем содержимое документов в контекст пользователя - оно будет в файлах
    
    return "\n".join(context_parts) if context_parts else "Данные отсутствуют"


@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """API endpoint для обработки сообщений чата через LM Studio"""
    try:
        # Проверяем размер запроса
        content_length = request.META.get('CONTENT_LENGTH', 0)
        if content_length:
            content_length = int(content_length)
            max_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 2621440)  # По умолчанию 2.5MB
            if content_length > max_size:
                return JsonResponse({
                    'success': False,
                    'error': f'Размер данных ({content_length / 1024 / 1024:.2f} MB) превышает максимально допустимый ({max_size / 1024 / 1024:.2f} MB). Пожалуйста, уменьшите размер файлов.'
                }, status=413)
        
        data = json.loads(request.body)
        message = data.get('message', '')
        chat_history = data.get('history', [])
        user_data = data.get('userData', {})  # Данные пользователя из localStorage
        files = data.get('files', [])  # Прикрепленные файлы
        
        # Настройки LM Studio
        LM_STUDIO_URL = getattr(settings, 'LM_STUDIO_URL', 'http://host.docker.internal:1234/v1/chat/completions')
        
        # Формируем историю сообщений для модели
        messages = []
        
        # Формируем контекст пользователя
        user_context = format_user_context(user_data)
        
        # Добавляем системный промпт с описанием возможностей (сокращенная версия для экономии токенов)
        system_prompt = """Ты - AI-помощник для бизнеса. Можешь:

1. АНАЛИЗИРОВАТЬ ДАННЫЕ:
   - ЧЕКИ: просматривать все операции, суммы, анализировать расходы и доходы, находить самые крупные операции
   - ИНВЕНТАРИЗАЦИЯ: просматривать товары, категории, количество, стоимость каждого товара, общую стоимость инвентаризации, анализировать складские остатки и их стоимость
   - СОТРУДНИКИ: просматривать список сотрудников, их должности, зарплаты, рассчитывать общий фонд оплаты труда
   - КАЛЕНДАРЬ: просматривать события, планировать встречи, напоминать о предстоящих событиях
   - НАЛОГИ: проверять задолженность по каждому налогу отдельно и общую сумму
   - КОММУНАЛЬНЫЕ УСЛУГИ: проверять задолженность по каждой услуге и общую сумму
   - ДОКУМЕНТЫ: работать с загруженными файлами, анализировать их содержимое (PDF, DOCX, XLSX, TXT, изображения и другие форматы)
   - БАЛАНСЫ: знать балансы обоих счетов пользователя

2. ВЫПОЛНЯТЬ ДЕЙСТВИЯ:
   - Создавать события в календаре: когда пользователь просит запланировать встречу или событие, используй формат: CREATE_EVENT: название|дата в формате ISO (YYYY-MM-DDTHH:mm)|описание
   - Редактировать события в календаре: КРИТИЧЕСКИ ВАЖНО - когда пользователь просит изменить или перенести встречу, ОБЯЗАТЕЛЬНО используй команду UPDATE_EVENT в формате JSON на отдельной строке:
     {"action": "UPDATE_EVENT", "event": "название_или_ID_события", "title": "новое_название", "date": "2024-12-25T15:00", "description": "новое_описание"}
     * Если нужно изменить только название: {"action": "UPDATE_EVENT", "event": "старое_название", "title": "новое_название"}
     * Если нужно перенести встречу на другой день/время: {"action": "UPDATE_EVENT", "event": "название_события", "date": "2024-12-25T15:00"}
     * Если нужно изменить описание/заметки/комментарий: {"action": "UPDATE_EVENT", "event": "название_события", "description": "новое_описание"}
     * ВАЖНО: При изменении описания ВСЕГДА указывай поле "description" с новым текстом описания
     * ВАЖНО: Описание может быть любым текстом, который пользователь просит добавить или изменить
     * Формат даты ОБЯЗАТЕЛЬНО: YYYY-MM-DDTHH:mm (например: 2024-12-25T15:00 для 25 декабря 2024 в 15:00)
     * ВАЖНО: При переносе встречи ВСЕГДА указывай поле "date" с полной датой и временем в формате ISO
     * Можно использовать название события или ID для поиска
     * Команда должна быть на отдельной строке в начале или конце ответа
   - Анализировать файлы: если пользователь прикрепил файл, анализируй его содержимое:
     * Текстовые файлы (TXT, CSV, JSON, XML, HTML, MD и др.) - читай и анализируй текст
     * PDF документы - извлекай и анализируй текст со всех страниц
     * DOCX документы - извлекай и анализируй текст и таблицы
     * XLSX таблицы - извлекай и анализируй данные из всех листов
     * Изображения - описывай содержимое, анализируй объекты, текст на изображениях, диаграммы и графики

3. ОТВЕЧАТЬ НА ВОПРОСЫ:
   - Отвечай кратко, по делу и дружелюбно
   - Используй конкретные данные из контекста пользователя
   - Если данных нет, сообщи об этом честно
   - При анализе чеков указывай конкретные суммы и даты
   - При работе с инвентаризацией указывай конкретные позиции и количество
   - При работе с сотрудниками называй их по именам и указывай зарплаты
   - При проверке задолженностей указывай точные суммы по каждому пункту

4. РЕДАКТИРОВАНИЕ СОБЫТИЙ - КРИТИЧЕСКИ ВАЖНО:
   - Когда пользователь просит изменить название встречи, ОБЯЗАТЕЛЬНО используй JSON команду UPDATE_EVENT с полем "title"
   - Когда пользователь просит перенести встречу на другой день/время, ОБЯЗАТЕЛЬНО используй JSON команду UPDATE_EVENT с полем "date"
   - Когда пользователь просит изменить описание/заметки/комментарий к встрече, ОБЯЗАТЕЛЬНО используй JSON команду UPDATE_EVENT с полем "description"
   - Когда пользователь просит добавить описание, изменить описание, обновить заметки, добавить комментарий - ВСЕГДА используй поле "description"
   - ВАЖНО: При переносе встречи дата ДОЛЖНА быть в формате ISO: YYYY-MM-DDTHH:mm (например: 2024-12-25T15:00)
   - ВАЖНО: При изменении названия ВСЕГДА указывай поле "title" с новым названием
   - ВАЖНО: При изменении описания ВСЕГДА указывай поле "description" с новым текстом описания (даже если это длинный текст)
   - ВАЖНО: Описание может содержать любой текст, который пользователь просит добавить или изменить
   - Если пользователь говорит "завтра", "послезавтра", "через неделю" - вычисли дату и используй формат ISO
   - Если пользователь говорит "в 15:00", "в 14:30" - добавь время к существующей дате или используй сегодняшнюю дату
   - Примеры JSON команд (должны быть на отдельной строке):
     * Изменить только название: {"action": "UPDATE_EVENT", "event": "старое_название", "title": "новое_название"}
     * Перенести встречу: {"action": "UPDATE_EVENT", "event": "название_события", "date": "2024-12-25T15:00"}
     * Перенести на завтра в 15:00: {"action": "UPDATE_EVENT", "event": "название_события", "date": "2024-12-26T15:00"}
     * Изменить описание: {"action": "UPDATE_EVENT", "event": "название_события", "description": "новое_описание"}
     * Добавить описание: {"action": "UPDATE_EVENT", "event": "название_события", "description": "текст описания"}
     * Изменить название и дату: {"action": "UPDATE_EVENT", "event": "название_события", "title": "новое_название", "date": "2024-12-25T15:00"}
     * Изменить все: {"action": "UPDATE_EVENT", "event": "название_события", "title": "новое_название", "date": "2024-12-25T15:00", "description": "новое_описание"}

ВАЖНО: Все суммы в рублях (₽). Для изменения встречи используй JSON: {"action": "UPDATE_EVENT", "event": "ID/название", "title": "...", "date": "YYYY-MM-DDTHH:mm", "description": "..."}

Данные пользователя:
""" + user_context[:1500]  # Ограничиваем контекст пользователя до 1500 символов
        
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # Обрабатываем файлы, если они есть
        image_files = []  # Список изображений для отправки в vision модель
        file_contents = []  # Список текстового содержимого файлов
        
        if files:
            for i, file in enumerate(files):
                try:
                    file_name = file.get('name', f'Файл {i+1}')
                    file_type = file.get('type', 'неизвестный тип')
                    file_data = file.get('data', '')
                    
                    if not file_data:
                        file_contents.append(f"Файл {i+1} ({file_name}): [Файл пуст или данные не получены]")
                        continue
                    
                    # Обрабатываем файл с помощью модуля file_processor
                    try:
                        extracted_text, image_base64 = process_file(file_name, file_type, file_data)
                    except Exception as e:
                        # Ошибка при обработке файла
                        logger.error(f"Ошибка при обработке файла '{file_name}': {str(e)}", exc_info=True)
                        error_msg = f"[Ошибка при обработке файла '{file_name}': {str(e)}]"
                        file_contents.append(f"Файл {i+1} ({file_name}): {error_msg}")
                        continue
                    
                    if image_base64:
                        # Это изображение - добавляем в список для отправки в vision модель
                        try:
                            # Формируем data URI для изображения
                            # Убеждаемся, что file_type правильный (например, image/jpeg, image/png)
                            if not file_type or file_type == 'неизвестный тип':
                                # Пытаемся определить тип по расширению
                                if file_name_lower.endswith('.png'):
                                    file_type = 'image/png'
                                elif file_name_lower.endswith('.jpg') or file_name_lower.endswith('.jpeg'):
                                    file_type = 'image/jpeg'
                                elif file_name_lower.endswith('.gif'):
                                    file_type = 'image/gif'
                                elif file_name_lower.endswith('.webp'):
                                    file_type = 'image/webp'
                                else:
                                    file_type = 'image/jpeg'  # По умолчанию
                            
                            # Убираем возможные пробелы и переносы строк из base64
                            image_base64_clean = image_base64.strip().replace('\n', '').replace('\r', '').replace(' ', '')
                            
                            image_files.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{file_type};base64,{image_base64_clean}"
                                }
                            })
                            # Также добавляем описание изображения в текст
                            file_contents.append(f"Файл {i+1} ({file_name}): {extracted_text}")
                        except Exception as e:
                            logger.error(f"Ошибка при подготовке изображения '{file_name}': {str(e)}", exc_info=True)
                            file_contents.append(f"Файл {i+1} ({file_name}): [Ошибка при подготовке изображения: {str(e)}]")
                    else:
                        # Это текстовый файл или документ - добавляем извлеченный текст
                        if extracted_text and not extracted_text.startswith('[') and not extracted_text.startswith('Изображение'):
                            # Ограничиваем размер текста (первые 2000 символов для каждого файла для экономии токенов)
                            text_preview = extracted_text[:2000]
                            if len(extracted_text) > 2000:
                                text_preview += "\n... [текст обрезан, показаны первые 2000 символов]"
                            file_contents.append(f"Файл {i+1} ({file_name}):\n{text_preview}")
                        else:
                            file_contents.append(f"Файл {i+1} ({file_name}): {extracted_text}")
                except Exception as e:
                    # Общая ошибка при обработке файла
                    logger.error(f"Критическая ошибка при обработке файла: {str(e)}", exc_info=True)
                    file_name = file.get('name', f'Файл {i+1}') if isinstance(file, dict) else f'Файл {i+1}'
                    file_contents.append(f"Файл {i+1} ({file_name}): [Критическая ошибка при обработке: {str(e)}]")
        
        # Добавляем историю чата (последние 3 сообщения для экономии токенов)
        # Ограничиваем размер каждого сообщения в истории
        for msg in chat_history[-3:]:
            msg_text = msg.get('text', '')
            # Ограничиваем размер сообщения в истории до 500 символов
            if len(msg_text) > 500:
                msg_text = msg_text[:500] + "... [обрезано]"
            messages.append({
                "role": "user" if msg.get('isUser') else "assistant",
                "content": msg_text
            })
        
        # Формируем финальное сообщение пользователя с файлами и текстом
        # Объединяем информацию о файлах и текст сообщения в одно сообщение
        final_content_parts = []
        
        # Добавляем информацию о файлах, если есть (ограничиваем общий размер)
        if file_contents:
            file_info = "Пользователь прикрепил файлы:\n\n" + "\n\n".join(file_contents)
            # Ограничиваем общий размер информации о файлах до 3000 символов
            if len(file_info) > 3000:
                file_info = file_info[:3000] + "\n... [информация о файлах обрезана]"
            final_content_parts.append({"type": "text", "text": file_info})
        
        # Добавляем текст сообщения, если есть (ограничиваем размер)
        if message:
            # Ограничиваем размер сообщения до 1000 символов
            message_limited = message[:1000] if len(message) > 1000 else message
            if len(message) > 1000:
                message_limited += "... [сообщение обрезано]"
            
            if final_content_parts:
                # Если уже есть текст о файлах, добавляем сообщение пользователя
                final_content_parts.append({"type": "text", "text": f"\n\nСообщение: {message_limited}"})
            else:
                final_content_parts.append({"type": "text", "text": message_limited})
        
        # Если нет ни файлов, ни сообщения, но есть изображения
        if not final_content_parts and image_files:
            final_content_parts.append({"type": "text", "text": "Проанализируй прикрепленные изображения"})
        
        # Добавляем изображения в конец
        final_content_parts.extend(image_files)
        
        # Создаем финальное сообщение
        if final_content_parts:
            # Если есть только один текстовый элемент и нет изображений, используем простой формат
            if len(final_content_parts) == 1 and final_content_parts[0]["type"] == "text":
                messages.append({
                    "role": "user",
                    "content": final_content_parts[0]["text"]
                })
            else:
                # Используем формат с массивом для vision модели
                messages.append({
                    "role": "user",
                    "content": final_content_parts
                })
        
        # Подготавливаем payload для запроса
        payload = {
            "model": "qwen3-vl-4b",  # Имя модели в LM Studio
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,  # Увеличили для более подробных ответов
            "stream": False
        }
        
        # Логируем запрос для отладки (без полных данных изображений)
        debug_messages = []
        for msg in messages:
            if isinstance(msg.get('content'), list):
                debug_content = []
                for item in msg['content']:
                    if item.get('type') == 'image_url':
                        debug_content.append({'type': 'image_url', 'image_url': {'url': '[BASE64_DATA]'}})
                    else:
                        debug_content.append(item)
                debug_messages.append({**msg, 'content': debug_content})
            else:
                debug_messages.append(msg)
        logger.debug(f"Отправка запроса в LM Studio: model={payload['model']}, messages_count={len(messages)}")
        
        # Отправляем запрос в LM Studio
        try:
            response = requests.post(
                LM_STUDIO_URL,
                json=payload,
                timeout=120  # Увеличили таймаут для обработки файлов
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при отправке запроса в LM Studio: {str(e)}")
            raise
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', 'Извините, не удалось получить ответ.')
            
            # Проверяем, нужно ли создать или обновить событие в календаре
            action_result = None
            if 'CREATE_EVENT:' in ai_response:
                # Извлекаем команду создания события
                parts = ai_response.split('CREATE_EVENT:')
                if len(parts) > 1:
                    event_data = parts[1].strip().split('|')
                    if len(event_data) >= 2:
                        action_result = {
                            'action': 'create_event',
                            'title': event_data[0].strip(),
                            'date': event_data[1].strip(),
                            'description': event_data[2].strip() if len(event_data) > 2 else ''
                        }
                        # Убираем команду из ответа
                        ai_response = parts[0].strip()
            
            # Пытаемся найти JSON команду UPDATE_EVENT (новый формат)
            # Ищем JSON объект с action: "UPDATE_EVENT" (может быть многострочным)
            # Пробуем несколько вариантов поиска JSON
            json_found = False
            json_str = None
            update_data = None
            
            # Вариант 1: Ищем полный JSON объект
            json_patterns = [
                r'\{\s*"action"\s*:\s*"UPDATE_EVENT"[^}]*\}',  # Простой вариант
                r'\{[^{}]*"action"\s*:\s*"UPDATE_EVENT"[^{}]*\}',  # С учетом возможных пробелов
            ]
            
            for pattern in json_patterns:
                json_match = re.search(pattern, ai_response, re.DOTALL | re.IGNORECASE)
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        update_data = json.loads(json_str)
                        if update_data.get('action') == 'UPDATE_EVENT':
                            json_found = True
                            break
                    except:
                        continue
            
            # Вариант 2: Если не нашли, пробуем найти JSON на отдельной строке
            if not json_found:
                lines = ai_response.split('\n')
                for line in lines:
                    line = line.strip()
                    if 'UPDATE_EVENT' in line and '{' in line and '}' in line:
                        try:
                            update_data = json.loads(line)
                            if update_data.get('action') == 'UPDATE_EVENT':
                                json_str = line
                                json_found = True
                                break
                        except:
                            continue
            
            if json_found and update_data:
                if update_data.get('action') == 'UPDATE_EVENT':
                    event_identifier = update_data.get('event', '').strip()
                    calendar_events = user_data.get('calendarEvents', [])
                    event_id = None
                    
                    # Сначала пытаемся найти по точному ID
                    for event in calendar_events:
                        if str(event.get('id', '')) == event_identifier:
                            event_id = str(event.get('id', ''))
                            break
                    
                    # Если не нашли по ID, ищем по названию (точное или частичное совпадение)
                    if not event_id:
                        event_identifier_lower = event_identifier.lower().strip()
                        # Сначала точное совпадение
                        for event in calendar_events:
                            event_title = event.get('title', '').lower().strip()
                            if event_title == event_identifier_lower:
                                event_id = str(event.get('id', ''))
                                break
                        
                        # Если не нашли точное, ищем частичное
                        if not event_id:
                            for event in calendar_events:
                                event_title = event.get('title', '').lower().strip()
                                if event_identifier_lower in event_title or event_title in event_identifier_lower:
                                    event_id = str(event.get('id', ''))
                                    break
                    
                    # Если все еще не нашли, берем последнее событие
                    if not event_id and calendar_events:
                        event_id = str(calendar_events[-1].get('id', ''))
                    
                    if event_id:
                        # Обрабатываем поля из JSON
                        # Для title и description проверяем наличие ключа, даже если значение пустое
                        new_title = None
                        if 'title' in update_data:
                            title_value = update_data.get('title')
                            # Разрешаем пустую строку для очистки названия
                            new_title = title_value.strip() if title_value else ''
                        
                        new_date = None
                        if 'date' in update_data:
                            new_date = update_data.get('date', '').strip() if update_data.get('date') else ''
                        
                        new_description = None
                        if 'description' in update_data:
                            # Разрешаем пустую строку для очистки описания
                            desc_value = update_data.get('description', '')
                            # Если значение есть (даже пустая строка), используем его
                            if desc_value is not None:
                                new_description = desc_value.strip() if desc_value else ''
                            else:
                                new_description = ''
                        
                        # Логируем для отладки
                        print(f"UPDATE_EVENT (JSON): event_id={event_id}")
                        print(f"  title: {new_title} (ключ присутствует: {'title' in update_data})")
                        print(f"  date: {new_date} (ключ присутствует: {'date' in update_data})")
                        print(f"  description: {new_description} (ключ присутствует: {'description' in update_data})")
                        
                        action_result = {
                            'action': 'update_event',
                            'id': event_id,
                            'title': new_title,
                            'date': new_date,
                            'description': new_description
                        }
                        # Убираем JSON команду из ответа
                        if json_str:
                            ai_response = ai_response.replace(json_str, '').strip()
            
            # Если не нашли JSON, пробуем старый формат UPDATE_EVENT: (для обратной совместимости)
            if not json_found and 'UPDATE_EVENT:' in ai_response:
                # Извлекаем команду обновления события (старый формат)
                parts = ai_response.split('UPDATE_EVENT:')
                if len(parts) > 1:
                    event_data_raw = parts[1].strip()
                    # Разделяем по |, но учитываем что могут быть пустые значения
                    event_data = []
                    current_part = ''
                    for char in event_data_raw:
                        if char == '|':
                            event_data.append(current_part.strip())
                            current_part = ''
                        else:
                            current_part += char
                    if current_part:
                        event_data.append(current_part.strip())
                    
                    if len(event_data) >= 1:
                        # Ищем событие по ID или названию
                        event_identifier = event_data[0].strip()
                        calendar_events = user_data.get('calendarEvents', [])
                        event_id = None
                        
                        # Сначала пытаемся найти по точному ID
                        for event in calendar_events:
                            if str(event.get('id', '')) == event_identifier:
                                event_id = str(event.get('id', ''))
                                break
                        
                        # Если не нашли по ID, ищем по названию (точное или частичное совпадение)
                        if not event_id:
                            event_identifier_lower = event_identifier.lower().strip()
                            # Сначала точное совпадение
                            for event in calendar_events:
                                event_title = event.get('title', '').lower().strip()
                                if event_title == event_identifier_lower:
                                    event_id = str(event.get('id', ''))
                                    break
                            
                            # Если не нашли точное, ищем частичное
                            if not event_id:
                                for event in calendar_events:
                                    event_title = event.get('title', '').lower().strip()
                                    if event_identifier_lower in event_title or event_title in event_identifier_lower:
                                        event_id = str(event.get('id', ''))
                                        break
                        
                        # Если все еще не нашли, берем последнее событие
                        if not event_id and calendar_events:
                            event_id = str(calendar_events[-1].get('id', ''))
                        
                        if event_id:
                            # Обрабатываем поля: title, date, description
                            new_title = event_data[1].strip() if len(event_data) > 1 and event_data[1].strip() else None
                            new_date = event_data[2].strip() if len(event_data) > 2 and event_data[2].strip() else None
                            new_description = event_data[3].strip() if len(event_data) > 3 and event_data[3].strip() else None
                            
                            # Логируем для отладки
                            print(f"UPDATE_EVENT (старый формат): event_id={event_id}, title={new_title}, date={new_date}, description={new_description}")
                            
                            action_result = {
                                'action': 'update_event',
                                'id': event_id,
                                'title': new_title,
                                'date': new_date,
                                'description': new_description
                            }
                        # Убираем команду из ответа
                        ai_response = parts[0].strip()
            
            return JsonResponse({
                'success': True,
                'response': ai_response,
                'action': action_result
            })
        else:
            # Ошибка от LM Studio - получаем детали
            error_details = f'Ошибка LM Studio: {response.status_code}'
            try:
                error_data = response.json()
                if isinstance(error_data, dict):
                    error_message = error_data.get('error', {}).get('message', '') if isinstance(error_data.get('error'), dict) else str(error_data.get('error', ''))
                    if error_message:
                        error_details = f'Ошибка LM Studio ({response.status_code}): {error_message}'
                    else:
                        error_details = f'Ошибка LM Studio ({response.status_code}): {json.dumps(error_data, ensure_ascii=False)}'
                else:
                    error_details = f'Ошибка LM Studio ({response.status_code}): {str(error_data)}'
            except:
                error_details = f'Ошибка LM Studio ({response.status_code}): {response.text[:500]}'
            
            logger.error(f"Ошибка от LM Studio: {error_details}")
            
            # Если это ошибка 400, проверяем причину
            if response.status_code == 400:
                # Проверяем, не связана ли ошибка с превышением контекста
                if 'context length' in error_details.lower() or 'context overflow' in error_details.lower() or '4096 tokens' in error_details:
                    return JsonResponse({
                        'success': False,
                        'error': 'Превышен лимит контекста модели (4096 токенов). Пожалуйста, сократите:\n- Размер прикрепленных файлов\n- Длину сообщения\n- Историю чата\n\nПопробуйте отправить меньше данных за раз.'
                    }, status=413)
                
                # Если это не ошибка контекста, возможно проблема с форматом изображений
                # Пробуем отправить без изображений, только с текстом
                if image_files:
                    logger.warning("Попытка отправить запрос без изображений из-за ошибки 400")
                    text_only_messages = []
                    for msg in messages:
                        if isinstance(msg.get('content'), list):
                            # Оставляем только текстовые части
                            text_parts = [item for item in msg['content'] if item.get('type') == 'text']
                            if text_parts:
                                text_content = '\n'.join([item.get('text', '') for item in text_parts])
                                text_content += '\n\n[Примечание: изображения не были обработаны из-за ошибки формата]'
                                text_only_messages.append({
                                    "role": msg.get('role', 'user'),
                                    "content": text_content
                                })
                        else:
                            text_only_messages.append(msg)
                    
                    try:
                        text_payload = {**payload, "messages": text_only_messages}
                        text_response = requests.post(LM_STUDIO_URL, json=text_payload, timeout=120)
                        if text_response.status_code == 200:
                            result = text_response.json()
                            ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                            return JsonResponse({
                                'success': True,
                                'response': ai_response + '\n\n[Примечание: изображения не были обработаны. Возможно, модель не поддерживает формат изображений или требуется другой формат.]',
                                'action': None
                            })
                    except:
                        pass
            
            return JsonResponse({
                'success': False,
                'error': error_details
            }, status=response.status_code if response.status_code < 500 else 500)
            
    except requests.exceptions.ConnectionError as e:
        error_msg = f'Не удалось подключиться к LM Studio ({LM_STUDIO_URL}). '
        error_msg += 'Проверьте:\n'
        error_msg += '1. LM Studio запущен и сервер активен (Status: Running)\n'
        error_msg += '2. Модель загружена и активна (Status: READY)\n'
        error_msg += '3. Порт 1234 не занят другим приложением\n'
        error_msg += f'4. URL в настройках правильный (текущий: {LM_STUDIO_URL})'
        return JsonResponse({
            'success': False,
            'error': error_msg,
            'details': str(e)
        }, status=503)
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'Превышено время ожидания ответа от LM Studio (120 сек). Модель может быть слишком медленной или перегруженной.'
        }, status=504)
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка запроса к LM Studio: {str(e)}',
            'url': LM_STUDIO_URL
        }, status=503)
    except ValueError as e:
        # Ошибка парсинга JSON (возможно, слишком большой запрос)
        if 'Request body exceeded' in str(e) or 'DATA_UPLOAD_MAX_MEMORY_SIZE' in str(e):
            return JsonResponse({
                'success': False,
                'error': 'Размер отправляемых данных слишком большой. Пожалуйста, уменьшите размер файлов (максимум 20 MB на файл, 40 MB общий размер).'
            }, status=413)
        return JsonResponse({
            'success': False,
            'error': f'Ошибка обработки данных: {str(e)}'
        }, status=400)
    except Exception as e:
        error_msg = str(e)
        # Проверяем, не связана ли ошибка с размером данных
        if 'Request body exceeded' in error_msg or 'DATA_UPLOAD_MAX_MEMORY_SIZE' in error_msg:
            return JsonResponse({
                'success': False,
                'error': 'Размер отправляемых данных слишком большой. Пожалуйста, уменьшите размер файлов (максимум 20 MB на файл, 40 MB общий размер).'
            }, status=413)
        return JsonResponse({
            'success': False,
            'error': f'Ошибка: {error_msg}',
            'type': type(e).__name__
        }, status=500)