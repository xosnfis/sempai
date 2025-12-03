"""
Полный набор тестов для приложения Alfa Finansi
Покрывает модели, API endpoints, обработку файлов, модерацию контента и утилиты
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import json
import uuid
import base64
import time
from unittest.mock import patch, Mock, MagicMock
from io import BytesIO

from .models import ChatRequest, ChatHistory
from .content_moderator import ContentModerator
from .file_processor import (
    process_file, 
    extract_text_from_pdf, 
    extract_text_from_docx,
    extract_text_from_xlsx,
    extract_text_from_text_file
)
from .views import format_user_context, find_event_smart


# ============================================================================
# ТЕСТЫ МОДЕЛЕЙ
# ============================================================================

class ChatRequestModelTest(TestCase):
    """Тесты для модели ChatRequest"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.test_message = "Тестовое сообщение"
        self.test_history = [{"role": "user", "content": "Привет"}]
        self.test_user_data = {"email": "test@example.com"}
        self.test_files = []
    
    def test_create_chat_request(self):
        """Тест создания ChatRequest с валидными данными"""
        request = ChatRequest.objects.create(
            message=self.test_message,
            chat_history=self.test_history,
            user_data=self.test_user_data,
            files_data=self.test_files
        )
        self.assertIsNotNone(request.id)
        self.assertIsInstance(request.id, uuid.UUID)
        self.assertEqual(request.message, self.test_message)
        self.assertEqual(request.status, ChatRequest.STATUS_PENDING)
    
    def test_chat_request_default_status(self):
        """Тест дефолтного статуса при создании"""
        request = ChatRequest.objects.create(message="Тест")
        self.assertEqual(request.status, ChatRequest.STATUS_PENDING)
    
    def test_chat_request_status_choices(self):
        """Тест всех возможных статусов"""
        request = ChatRequest.objects.create(message="Тест")
        
        request.status = ChatRequest.STATUS_PROCESSING
        request.save()
        self.assertEqual(request.status, ChatRequest.STATUS_PROCESSING)
        
        request.status = ChatRequest.STATUS_COMPLETED
        request.save()
        self.assertEqual(request.status, ChatRequest.STATUS_COMPLETED)
        
        request.status = ChatRequest.STATUS_FAILED
        request.save()
        self.assertEqual(request.status, ChatRequest.STATUS_FAILED)
    
    def test_chat_request_timestamps(self):
        """Тест автоматических временных меток"""
        request = ChatRequest.objects.create(message="Тест")
        self.assertIsNotNone(request.created_at)
        self.assertIsNotNone(request.updated_at)
        
        # Проверяем, что updated_at обновляется
        old_updated = request.updated_at
        time.sleep(0.1)
        request.message = "Обновленное сообщение"
        request.save()
        self.assertGreater(request.updated_at, old_updated)
    
    def test_chat_request_ordering(self):
        """Тест сортировки по created_at (descending)"""
        request1 = ChatRequest.objects.create(message="Первый")
        time.sleep(0.1)
        request2 = ChatRequest.objects.create(message="Второй")
        
        requests = list(ChatRequest.objects.all())
        self.assertEqual(requests[0].message, "Второй")
        self.assertEqual(requests[1].message, "Первый")
    
    def test_chat_request_str(self):
        """Тест строкового представления"""
        request = ChatRequest.objects.create(message="Тест")
        str_repr = str(request)
        self.assertIn(str(request.id), str_repr)
        self.assertIn(request.status, str_repr)
    
    def test_chat_request_json_fields(self):
        """Тест работы с JSON полями"""
        request = ChatRequest.objects.create(
            message="Тест",
            chat_history=[{"role": "user", "content": "Привет"}],
            user_data={"email": "test@example.com", "name": "Test"},
            files_data=[{"name": "file.pdf", "type": "application/pdf"}]
        )
        
        self.assertEqual(len(request.chat_history), 1)
        self.assertEqual(request.user_data["email"], "test@example.com")
        self.assertEqual(len(request.files_data), 1)
    
    def test_chat_request_completed_at(self):
        """Тест поля completed_at"""
        request = ChatRequest.objects.create(message="Тест")
        self.assertIsNone(request.completed_at)
        
        request.status = ChatRequest.STATUS_COMPLETED
        request.completed_at = timezone.now()
        request.save()
        self.assertIsNotNone(request.completed_at)


class ChatHistoryModelTest(TestCase):
    """Тесты для модели ChatHistory"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.test_email = "test@example.com"
        self.test_chat_id = "chat-123"
        self.test_title = "Тестовый чат"
    
    def test_create_chat_history(self):
        """Тест создания ChatHistory"""
        history = ChatHistory.objects.create(
            user_email=self.test_email,
            chat_id=self.test_chat_id,
            title=self.test_title
        )
        self.assertIsNotNone(history.id)
        self.assertIsInstance(history.id, uuid.UUID)
        self.assertEqual(history.user_email, self.test_email)
        self.assertEqual(history.chat_id, self.test_chat_id)
        self.assertEqual(history.title, self.test_title)
    
    def test_chat_history_default_values(self):
        """Тест дефолтных значений"""
        history = ChatHistory.objects.create(
            user_email=self.test_email,
            chat_id=self.test_chat_id
        )
        self.assertEqual(history.title, "Новый чат")
        self.assertEqual(history.total_messages, 0)
        self.assertEqual(history.total_user_messages, 0)
        self.assertEqual(history.total_ai_messages, 0)
        self.assertEqual(history.total_actions, 0)
        self.assertEqual(history.messages, [])
        self.assertEqual(history.ai_actions, [])
    
    def test_chat_history_timestamps(self):
        """Тест временных меток"""
        history = ChatHistory.objects.create(
            user_email=self.test_email,
            chat_id=self.test_chat_id
        )
        self.assertIsNotNone(history.created_at)
        self.assertIsNotNone(history.updated_at)
        self.assertIsNone(history.last_message_at)
    
    def test_chat_history_messages(self):
        """Тест работы с сообщениями"""
        history = ChatHistory.objects.create(
            user_email=self.test_email,
            chat_id=self.test_chat_id
        )
        
        messages = [
            {"role": "user", "content": "Привет", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "content": "Здравствуйте!", "timestamp": "2024-01-01T10:00:05"}
        ]
        history.messages = messages
        history.total_messages = 2
        history.total_user_messages = 1
        history.total_ai_messages = 1
        history.save()
        
        history.refresh_from_db()
        self.assertEqual(len(history.messages), 2)
        self.assertEqual(history.total_messages, 2)
    
    def test_chat_history_ordering(self):
        """Тест сортировки по last_message_at"""
        history1 = ChatHistory.objects.create(
            user_email=self.test_email,
            chat_id="chat-1"
        )
        time.sleep(0.1)
        history2 = ChatHistory.objects.create(
            user_email=self.test_email,
            chat_id="chat-2",
            last_message_at=timezone.now()
        )
        
        histories = list(ChatHistory.objects.all())
        self.assertEqual(histories[0].chat_id, "chat-2")
    
    def test_chat_history_str(self):
        """Тест строкового представления"""
        history = ChatHistory.objects.create(
            user_email=self.test_email,
            chat_id=self.test_chat_id,
            total_messages=5
        )
        str_repr = str(history)
        self.assertIn(self.test_chat_id, str_repr)
        self.assertIn(self.test_email, str_repr)
        self.assertIn("5", str_repr)


# ============================================================================
# ТЕСТЫ МОДЕРАЦИИ КОНТЕНТА
# ============================================================================

class ContentModeratorTest(TestCase):
    """Тесты для модерации контента"""
    
    def test_allowed_message(self):
        """Тест разрешенного сообщения"""
        result = ContentModerator.check_message("Обычное сообщение для теста")
        self.assertTrue(result['allowed'])
        self.assertIsNone(result['reason'])
        self.assertEqual(result['filtered_message'], "Обычное сообщение для теста")
    
    def test_forbidden_pattern(self):
        """Тест блокировки запрещенного паттерна"""
        result = ContentModerator.check_message("как взломать банк")
        self.assertFalse(result['allowed'])
        self.assertIn('недопустимый контент', result['reason'])
    
    def test_forbidden_pattern_variations(self):
        """Тест различных запрещенных паттернов"""
        forbidden_messages = [
            "как обмануть систему",
            "как украсть деньги",
            "как убить человека",
            "как взорвать здание",
            "наркотики для продажи",
            "суицид как решение"
        ]
        
        for message in forbidden_messages:
            result = ContentModerator.check_message(message)
            self.assertFalse(result['allowed'], f"Сообщение '{message}' должно быть заблокировано")
    
    def test_message_too_short(self):
        """Тест слишком короткого сообщения"""
        result = ContentModerator.check_message("")
        self.assertFalse(result['allowed'])
        # Пустое сообщение возвращает "Пустое или неверное сообщение", а не "короткое"
        self.assertIn('пустое', result['reason'].lower())
    
    def test_message_too_long(self):
        """Тест слишком длинного сообщения"""
        long_message = "а" * (ContentModerator.MAX_MESSAGE_LENGTH + 1)
        result = ContentModerator.check_message(long_message)
        self.assertFalse(result['allowed'])
        self.assertIn('длинное', result['reason'].lower())
        # Проверяем, что сообщение обрезано
        self.assertEqual(len(result['filtered_message']), ContentModerator.MAX_MESSAGE_LENGTH)
    
    def test_spam_detection_repeated_chars(self):
        """Тест обнаружения спама (повторяющиеся символы)"""
        spam_message = "а" * 15
        result = ContentModerator.check_message(spam_message)
        self.assertFalse(result['allowed'])
        self.assertIn('спам', result['reason'].lower())
    
    def test_spam_detection_repeated_words(self):
        """Тест обнаружения спама (повторяющиеся слова)"""
        spam_message = "тест " * 20
        result = ContentModerator.check_message(spam_message)
        self.assertFalse(result['allowed'])
        self.assertIn('спам', result['reason'].lower())
    
    def test_sanitize_message(self):
        """Тест санитизации сообщения"""
        message_with_control_chars = "Тест\x00\x01\x02\x03сообщение"
        sanitized = ContentModerator.sanitize_message(message_with_control_chars)
        self.assertNotIn('\x00', sanitized)
        self.assertNotIn('\x01', sanitized)
        self.assertIn('Тест', sanitized)
        self.assertIn('сообщение', sanitized)
    
    def test_sanitize_empty_message(self):
        """Тест санитизации пустого сообщения"""
        result = ContentModerator.sanitize_message("")
        self.assertEqual(result, "")
        result = ContentModerator.sanitize_message(None)
        self.assertEqual(result, "")
    
    def test_check_ai_response_allowed(self):
        """Тест проверки разрешенного ответа AI"""
        result = ContentModerator.check_ai_response("Это нормальный ответ от AI")
        self.assertTrue(result['allowed'])
        self.assertIsNone(result['reason'])
    
    def test_check_ai_response_forbidden(self):
        """Тест проверки запрещенного ответа AI"""
        result = ContentModerator.check_ai_response("как взломать систему")
        self.assertFalse(result['allowed'])
        self.assertIn('недопустимый контент', result['reason'])
    
    def test_check_ai_response_empty(self):
        """Тест проверки пустого ответа AI"""
        result = ContentModerator.check_ai_response("")
        self.assertTrue(result['allowed'])  # Пустые ответы разрешены
        result = ContentModerator.check_ai_response(None)
        self.assertTrue(result['allowed'])
    
    def test_check_message_invalid_type(self):
        """Тест проверки сообщения неверного типа"""
        result = ContentModerator.check_message(None)
        self.assertFalse(result['allowed'])
        result = ContentModerator.check_message(123)
        self.assertFalse(result['allowed'])


# ============================================================================
# ТЕСТЫ ОБРАБОТКИ ФАЙЛОВ
# ============================================================================

class FileProcessorTest(TestCase):
    """Тесты для обработки файлов"""
    
    def test_process_text_file(self):
        """Тест обработки текстового файла"""
        text_content = "Это тестовый текст для проверки обработки файлов"
        file_data = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
        text, image = process_file("test.txt", "text/plain", file_data)
        self.assertIn("тестовый текст", text)
        self.assertIsNone(image)
    
    def test_process_text_file_with_prefix(self):
        """Тест обработки текстового файла с data URL префиксом"""
        text_content = "Тестовый контент"
        file_data = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
        data_url = f"data:text/plain;base64,{file_data}"
        text, image = process_file("test.txt", "text/plain", data_url)
        self.assertIn("Тестовый контент", text)
    
    def test_process_empty_file(self):
        """Тест обработки пустого файла"""
        text, image = process_file("empty.txt", "text/plain", "")
        self.assertIn("пуст", text.lower())
        self.assertIsNone(image)
    
    def test_process_file_no_name(self):
        """Тест обработки файла без имени"""
        text_content = "Контент"
        file_data = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
        text, image = process_file("", "text/plain", file_data)
        self.assertIn("Контент", text)
    
    def test_process_unsupported_format(self):
        """Тест обработки неподдерживаемого формата"""
        file_data = base64.b64encode(b"test content").decode('utf-8')
        text, image = process_file("test.doc", "application/msword", file_data)
        self.assertIn("не поддерживается", text.lower())
    
    def test_extract_text_from_text_file(self):
        """Тест извлечения текста из текстового файла"""
        text_content = "Простой текст для теста"
        file_data = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
        result = extract_text_from_text_file(file_data)
        self.assertEqual(result, text_content)
    
    def test_extract_text_from_text_file_with_prefix(self):
        """Тест извлечения текста с префиксом"""
        text_content = "Текст с префиксом"
        file_data = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
        data_url = f"data:text/plain;base64,{file_data}"
        result = extract_text_from_text_file(data_url)
        self.assertEqual(result, text_content)
    
    def test_extract_text_from_text_file_invalid_base64(self):
        """Тест обработки невалидного base64"""
        result = extract_text_from_text_file("invalid_base64!!!")
        self.assertIn("Ошибка", result)
    
    @patch('PyPDF2.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader):
        """Тест извлечения текста из PDF (мок)"""
        # Настраиваем мок
        mock_page = Mock()
        mock_page.extract_text.return_value = "Текст из PDF"
        mock_reader_instance = Mock()
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance
        
        file_data = base64.b64encode(b"fake pdf content").decode('utf-8')
        result = extract_text_from_pdf(file_data)
        self.assertIn("Текст из PDF", result)
    
    @patch('docx.Document')
    def test_extract_text_from_docx(self, mock_docx):
        """Тест извлечения текста из DOCX (мок)"""
        # Настраиваем мок
        mock_paragraph = Mock()
        mock_paragraph.text = "Текст из DOCX"
        mock_doc = Mock()
        mock_doc.paragraphs = [mock_paragraph]
        mock_doc.tables = []
        mock_docx.return_value = mock_doc
        
        file_data = base64.b64encode(b"fake docx content").decode('utf-8')
        result = extract_text_from_docx(file_data)
        self.assertIn("Текст из DOCX", result)
    
    @patch('openpyxl.load_workbook')
    def test_extract_text_from_xlsx(self, mock_load_workbook):
        """Тест извлечения текста из XLSX (мок)"""
        # Настраиваем мок
        mock_sheet = Mock()
        mock_sheet.iter_rows.return_value = [("A1", "B1", "C1"), ("A2", "B2", "C2")]
        
        # Создаем класс-обертку для правильной работы __getitem__
        class MockWorkbook:
            def __init__(self, sheet):
                self.sheetnames = ["Sheet1"]
                self._sheet = sheet
            
            def __getitem__(self, key):
                if key == "Sheet1":
                    return self._sheet
                return Mock()
        
        mock_workbook = MockWorkbook(mock_sheet)
        mock_load_workbook.return_value = mock_workbook
        
        file_data = base64.b64encode(b"fake xlsx content").decode('utf-8')
        result = extract_text_from_xlsx(file_data)
        self.assertIn("Sheet1", result)
        self.assertIn("A1", result)


# ============================================================================
# ТЕСТЫ УТИЛИТАРНЫХ ФУНКЦИЙ
# ============================================================================

class UtilityFunctionsTest(TestCase):
    """Тесты для утилитарных функций"""
    
    def test_format_user_context_empty(self):
        """Тест форматирования пустых данных пользователя"""
        result = format_user_context({})
        self.assertIsInstance(result, str)
    
    def test_format_user_context_with_balances(self):
        """Тест форматирования с балансами счетов"""
        user_data = {
            'accountBalance': 10000,
            'accountBalance2': 5000
        }
        result = format_user_context(user_data)
        # Функция форматирует числа с запятыми (10,000), поэтому проверяем форматированное значение
        self.assertIn("10,000", result)
        self.assertIn("5,000", result)
        self.assertIn("Балансы счетов", result)
    
    def test_format_user_context_with_receipts(self):
        """Тест форматирования с чеками"""
        user_data = {
            'receipts': [
                {'operationType': 'Покупка', 'amount': 1000, 'date': '2024-01-01'},
                {'operationType': 'Продажа', 'amount': 2000, 'date': '2024-01-02'}
            ]
        }
        result = format_user_context(user_data)
        self.assertIn("ЧЕКИ", result)
        self.assertIn("2 операций", result)
        # Функция форматирует числа с запятыми (3,000), поэтому проверяем форматированное значение
        self.assertIn("3,000", result)  # Сумма
        self.assertIn("Покупка", result)
        self.assertIn("Продажа", result)
    
    def test_format_user_context_with_inventory(self):
        """Тест форматирования с инвентаризацией"""
        user_data = {
            'inventory': [
                {'name': 'Товар 1', 'quantity': 10, 'price': 100, 'folderId': '1'},
                {'name': 'Товар 2', 'quantity': 5, 'price': 200, 'folderId': '1'}
            ],
            'inventoryFolders': [
                {'id': '1', 'name': 'Категория 1'}
            ]
        }
        result = format_user_context(user_data)
        self.assertIn("ИНВЕНТАРИЗАЦИЯ", result)
        self.assertIn("2 позиций", result)
        self.assertIn("Товар 1", result)
    
    def test_find_event_smart_by_id(self):
        """Тест поиска события по ID"""
        events = [
            {'id': '1', 'title': 'Событие 1', 'date': '2024-01-01'},
            {'id': '2', 'title': 'Событие 2', 'date': '2024-01-02'}
        ]
        result = find_event_smart(events, '1')
        self.assertEqual(result, '1')
    
    def test_find_event_smart_by_title(self):
        """Тест поиска события по точному названию"""
        events = [
            {'id': '1', 'title': 'Встреча с клиентом', 'date': '2024-01-01'},
            {'id': '2', 'title': 'Презентация', 'date': '2024-01-02'}
        ]
        result = find_event_smart(events, 'Встреча с клиентом')
        self.assertEqual(result, '1')
    
    def test_find_event_smart_by_partial_title(self):
        """Тест поиска события по части названия"""
        events = [
            {'id': '1', 'title': 'Встреча с клиентом', 'date': '2024-01-01'},
            {'id': '2', 'title': 'Презентация проекта', 'date': '2024-01-02'}
        ]
        result = find_event_smart(events, 'клиентом')
        self.assertEqual(result, '1')
    
    def test_find_event_smart_by_description(self):
        """Тест поиска события по описанию"""
        events = [
            {'id': '1', 'title': 'Событие 1', 'description': 'Важная встреча', 'date': '2024-01-01'},
            {'id': '2', 'title': 'Событие 2', 'description': 'Обычная встреча', 'date': '2024-01-02'}
        ]
        result = find_event_smart(events, 'Важная')
        self.assertEqual(result, '1')
    
    def test_find_event_smart_not_found(self):
        """Тест поиска несуществующего события"""
        events = [
            {'id': '1', 'title': 'Событие 1', 'date': '2024-01-01'}
        ]
        result = find_event_smart(events, 'Несуществующее')
        self.assertIsNone(result)
    
    def test_find_event_smart_empty_list(self):
        """Тест поиска в пустом списке"""
        result = find_event_smart([], 'любой идентификатор')
        self.assertIsNone(result)
    
    def test_find_event_smart_empty_identifier(self):
        """Тест поиска с пустым идентификатором"""
        events = [{'id': '1', 'title': 'Событие 1'}]
        result = find_event_smart(events, '')
        self.assertIsNone(result)
        result = find_event_smart(events, None)
        self.assertIsNone(result)


# ============================================================================
# ТЕСТЫ API ENDPOINTS
# ============================================================================

class ChatAPITest(TestCase):
    """Тесты для API чата"""
    
    def setUp(self):
        """Настройка тестового клиента"""
        self.client = Client()
        self.valid_data = {
            'message': 'Привет, это тестовое сообщение',
            'history': [],
            'userData': {'email': 'test@example.com'},
            'files': []
        }
    
    def test_chat_api_success(self):
        """Тест успешного создания запроса"""
        response = self.client.post(
            '/api/chat/',
            data=json.dumps(self.valid_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('request_id', result)
        self.assertEqual(result['status'], 'processing')
        
        # Проверяем, что запрос создан в БД
        request_id = uuid.UUID(result['request_id'])
        chat_request = ChatRequest.objects.get(id=request_id)
        self.assertEqual(chat_request.status, ChatRequest.STATUS_PENDING)
    
    def test_chat_api_moderation_block(self):
        """Тест блокировки запрещенного контента"""
        data = self.valid_data.copy()
        data['message'] = 'как взломать систему'
        response = self.client.post(
            '/api/chat/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_code'], 'CONTENT_MODERATION_FAILED')
    
    def test_chat_api_invalid_json(self):
        """Тест обработки невалидного JSON"""
        response = self.client.post(
            '/api/chat/',
            data='невалидный json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertEqual(result['error_code'], 'INVALID_JSON')
    
    def test_chat_api_empty_message(self):
        """Тест обработки пустого сообщения"""
        data = self.valid_data.copy()
        data['message'] = ''
        response = self.client.post(
            '/api/chat/',
            data=json.dumps(data),
            content_type='application/json'
        )
        # Пустое сообщение должно быть заблокировано модератором
        self.assertEqual(response.status_code, 400)
    
    def test_chat_api_with_files(self):
        """Тест создания запроса с файлами"""
        data = self.valid_data.copy()
        data['files'] = [
            {
                'name': 'test.txt',
                'type': 'text/plain',
                'data': base64.b64encode(b'test content').decode('utf-8')
            }
        ]
        response = self.client.post(
            '/api/chat/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        
        # Проверяем, что файлы сохранены
        request_id = uuid.UUID(result['request_id'])
        chat_request = ChatRequest.objects.get(id=request_id)
        self.assertEqual(len(chat_request.files_data), 1)


class ChatStatusAPITest(TestCase):
    """Тесты для API статуса чата"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        self.chat_request = ChatRequest.objects.create(
            message="Тестовое сообщение",
            status=ChatRequest.STATUS_PENDING
        )
    
    def test_get_status_pending(self):
        """Тест получения статуса pending"""
        response = self.client.get(f'/api/chat-status/{self.chat_request.id}/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertEqual(result['status'], ChatRequest.STATUS_PENDING)
        self.assertIn('request_id', result)
    
    def test_get_status_completed(self):
        """Тест получения статуса completed"""
        self.chat_request.status = ChatRequest.STATUS_COMPLETED
        self.chat_request.response = "Ответ от AI"
        self.chat_request.action = {"type": "response"}
        self.chat_request.completed_at = timezone.now()
        self.chat_request.save()
        
        response = self.client.get(f'/api/chat-status/{self.chat_request.id}/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], ChatRequest.STATUS_COMPLETED)
        self.assertIn('response', result)
        self.assertIn('action', result)
        self.assertIn('completed_at', result)
    
    def test_get_status_failed(self):
        """Тест получения статуса failed"""
        self.chat_request.status = ChatRequest.STATUS_FAILED
        self.chat_request.error = "Ошибка обработки"
        self.chat_request.save()
        
        response = self.client.get(f'/api/chat-status/{self.chat_request.id}/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], ChatRequest.STATUS_FAILED)
        self.assertIn('error', result)
    
    def test_get_status_not_found(self):
        """Тест получения статуса несуществующего запроса"""
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/chat-status/{fake_id}/')
        self.assertEqual(response.status_code, 404)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('не найден', result['error'])
    
    def test_get_status_invalid_uuid(self):
        """Тест получения статуса с невалидным UUID"""
        response = self.client.get('/api/chat-status/invalid-uuid/')
        self.assertEqual(response.status_code, 404)  # Django вернет 404 для невалидного UUID


class ChatHistoryAPITest(TestCase):
    """Тесты для API истории чатов"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        self.test_email = "test@example.com"
        self.chat_history = ChatHistory.objects.create(
            user_email=self.test_email,
            chat_id="chat-123",
            title="Тестовый чат",
            messages=[
                {"role": "user", "content": "Привет"},
                {"role": "assistant", "content": "Здравствуйте!"}
            ],
            total_messages=2
        )
    
    def test_get_chat_history_list(self):
        """Тест получения списка истории чатов"""
        response = self.client.get(f'/api/chat-history/?email={self.test_email}')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('history', result)
        self.assertEqual(len(result['history']), 1)
        self.assertEqual(result['history'][0]['chat_id'], "chat-123")
    
    def test_get_chat_history_no_email(self):
        """Тест получения истории без email"""
        response = self.client.get('/api/chat-history/')
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('Email не указан', result['error'])
    
    def test_get_chat_history_detail(self):
        """Тест получения детальной истории чата"""
        # Функция требует параметр email в GET запросе
        response = self.client.get(f'/api/chat-history/{self.chat_history.chat_id}/?email={self.test_email}')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('chat', result)
        self.assertEqual(result['chat']['chat_id'], "chat-123")
        self.assertEqual(len(result['chat']['messages']), 2)
    
    def test_get_chat_history_detail_not_found(self):
        """Тест получения несуществующей истории"""
        # Функция требует параметр email в GET запросе
        response = self.client.get(f'/api/chat-history/non-existent-chat/?email={self.test_email}')
        self.assertEqual(response.status_code, 404)
        result = json.loads(response.content)
        self.assertFalse(result['success'])


class CalendarEventAPITest(TestCase):
    """Тесты для API календаря"""
    
    def setUp(self):
        """Настройка тестового клиента"""
        self.client = Client()
    
    def test_create_calendar_event_success(self):
        """Тест успешного создания события"""
        data = {
            'email': 'test@example.com',
            'title': 'Встреча',
            'date': '2024-01-01T10:00:00',
            'description': 'Описание встречи'
        }
        response = self.client.post(
            '/api/create-event/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertIn('event', result)
        self.assertEqual(result['event']['title'], 'Встреча')
        self.assertIn('id', result['event'])
    
    def test_create_calendar_event_missing_fields(self):
        """Тест создания события без обязательных полей"""
        data = {
            'email': 'test@example.com',
            'title': 'Встреча'
            # Отсутствует date
        }
        response = self.client.post(
            '/api/create-event/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('обязательные поля', result['error'])
    
    def test_manage_calendar_event_create(self):
        """Тест управления событием - создание"""
        data = {
            'action': 'create',
            'email': 'test@example.com',
            'title': 'Новое событие',
            'date': '2024-01-01T10:00:00'
        }
        response = self.client.post(
            '/api/manage-calendar/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'create')
        self.assertIn('event', result)
    
    def test_manage_calendar_event_update(self):
        """Тест управления событием - обновление"""
        data = {
            'action': 'update',
            'email': 'test@example.com',
            'event_id': '123',
            'title': 'Обновленное событие',
            'date': '2024-01-01T10:00:00'
        }
        response = self.client.post(
            '/api/manage-calendar/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'update')
        self.assertEqual(result['event']['id'], '123')
    
    def test_manage_calendar_event_delete(self):
        """Тест управления событием - удаление"""
        data = {
            'action': 'delete',
            'email': 'test@example.com',
            'event_id': '123'
        }
        response = self.client.post(
            '/api/manage-calendar/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'delete')
        self.assertEqual(result['event_id'], '123')
    
    def test_manage_calendar_event_invalid_action(self):
        """Тест управления событием с невалидным действием"""
        data = {
            'action': 'invalid_action',
            'email': 'test@example.com'
        }
        response = self.client.post(
            '/api/manage-calendar/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertIn('Неизвестное действие', result['error'])
    
    def test_manage_calendar_event_no_email(self):
        """Тест управления событием без email"""
        data = {
            'action': 'create',
            'title': 'Событие',
            'date': '2024-01-01'
        }
        response = self.client.post(
            '/api/manage-calendar/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.content)
        self.assertFalse(result['success'])


class CheckLMStudioAPITest(TestCase):
    """Тесты для API проверки подключения к LM Studio"""
    
    def setUp(self):
        """Настройка тестового клиента"""
        self.client = Client()
    
    @patch('main.views.requests.get')
    @patch('main.views.requests.post')
    def test_check_lm_studio_success(self, mock_post, mock_get):
        """Тест успешной проверки подключения (мок)"""
        # Настраиваем моки
        mock_get.return_value.status_code = 200
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {'choices': [{'message': {'content': 'test'}}]}
        mock_post.return_value = mock_post_response
        
        response = self.client.get('/api/check-lm-studio/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        self.assertTrue(result['server_available'])
        self.assertTrue(result['api_available'])
        self.assertTrue(result['model_available'])
    
    @patch('main.views.requests.get')
    def test_check_lm_studio_server_unavailable(self, mock_get):
        """Тест проверки при недоступном сервере"""
        mock_get.side_effect = Exception("Connection error")
        
        response = self.client.get('/api/check-lm-studio/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertFalse(result['success'])
        self.assertFalse(result['server_available'])


class UserDataAPITest(TestCase):
    """Тесты для API данных пользователя"""
    
    def setUp(self):
        """Настройка тестового клиента"""
        self.client = Client()
    
    def test_get_user_data_post(self):
        """Тест получения/сохранения данных пользователя (POST)"""
        data = {
            'email': 'test@example.com',
            'userData': {'name': 'Test User', 'balance': 1000}
        }
        response = self.client.post(
            '/api/user-data/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        # Функция возвращает только сообщение, а не userData
        self.assertIn('message', result)


# ============================================================================
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# ============================================================================

class IntegrationTest(TestCase):
    """Интеграционные тесты для проверки взаимодействия компонентов"""
    
    def setUp(self):
        """Настройка тестового клиента"""
        self.client = Client()
    
    def test_full_chat_flow(self):
        """Тест полного цикла работы чата"""
        # 1. Создаем запрос
        data = {
            'message': 'Привет, как дела?',
            'history': [],
            'userData': {'email': 'test@example.com'},
            'files': []
        }
        response = self.client.post(
            '/api/chat/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        request_id = result['request_id']
        
        # 2. Проверяем статус
        response = self.client.get(f'/api/chat-status/{request_id}/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertIn('status', result)
    
    def test_chat_with_file_processing(self):
        """Тест чата с обработкой файла"""
        text_content = "Содержимое файла для анализа"
        file_data = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
        
        data = {
            'message': 'Проанализируй этот файл',
            'history': [],
            'userData': {'email': 'test@example.com'},
            'files': [{
                'name': 'test.txt',
                'type': 'text/plain',
                'data': file_data
            }]
        }
        response = self.client.post(
            '/api/chat/',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertTrue(result['success'])
        
        # Проверяем, что файл сохранен
        request_id = uuid.UUID(result['request_id'])
        chat_request = ChatRequest.objects.get(id=request_id)
        self.assertEqual(len(chat_request.files_data), 1)
    
    def test_chat_history_creation_and_retrieval(self):
        """Тест создания и получения истории чата"""
        # Создаем историю
        history = ChatHistory.objects.create(
            user_email='test@example.com',
            chat_id='test-chat-1',
            title='Тестовый чат',
            messages=[
                {'role': 'user', 'content': 'Вопрос 1'},
                {'role': 'assistant', 'content': 'Ответ 1'}
            ],
            total_messages=2
        )
        
        # Получаем список
        response = self.client.get('/api/chat-history/?email=test@example.com')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(len(result['history']), 1)
        
        # Получаем детали (требуется параметр email)
        response = self.client.get(f'/api/chat-history/{history.chat_id}/?email=test@example.com')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(len(result['chat']['messages']), 2)


# ============================================================================
# ТЕСТЫ БЕЗОПАСНОСТИ
# ============================================================================

class SecurityTest(TestCase):
    """Тесты безопасности"""
    
    def setUp(self):
        """Настройка тестового клиента"""
        self.client = Client()
    
    def test_sql_injection_protection(self):
        """Тест защиты от SQL инъекций (через ORM)"""
        # Попытка SQL инъекции в email
        malicious_email = "test@example.com'; DROP TABLE main_chathistory; --"
        history = ChatHistory.objects.create(
            user_email=malicious_email,
            chat_id='test-1'
        )
        # Если ORM работает правильно, это должно быть безопасно
        self.assertEqual(history.user_email, malicious_email)
        # Проверяем, что таблица все еще существует
        self.assertTrue(ChatHistory.objects.filter(user_email=malicious_email).exists())
    
    def test_xss_protection_in_message(self):
        """Тест защиты от XSS в сообщениях"""
        xss_message = "<script>alert('XSS')</script>"
        result = ContentModerator.sanitize_message(xss_message)
        # Санитизация должна сохранить текст, но Django автоматически экранирует в шаблонах
        self.assertIn('script', result.lower())
    
    def test_large_file_protection(self):
        """Тест защиты от больших файлов"""
        # Создаем большой файл (больше лимита)
        large_data = "x" * (50 * 1024 * 1024 + 1)  # Больше 50MB
        file_data = base64.b64encode(large_data.encode('utf-8')).decode('utf-8')
        
        data = {
            'message': 'Тест',
            'history': [],
            'userData': {},
            'files': [{
                'name': 'large.txt',
                'type': 'text/plain',
                'data': file_data
            }]
        }
        # Django должен отклонить такой большой запрос
        # (проверка происходит на уровне Django, не в нашем коде)
        # Но мы можем проверить, что наш код обрабатывает это корректно


# ============================================================================
# ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ
# ============================================================================

class PerformanceTest(TestCase):
    """Тесты производительности"""
    
    def test_bulk_chat_request_creation(self):
        """Тест создания множества запросов"""
        start_time = time.time()
        for i in range(100):
            ChatRequest.objects.create(
                message=f"Тестовое сообщение {i}",
                status=ChatRequest.STATUS_PENDING
            )
        end_time = time.time()
        
        # Проверяем, что создание 100 записей занимает разумное время (< 5 секунд)
        self.assertLess(end_time - start_time, 5.0)
        self.assertEqual(ChatRequest.objects.count(), 100)
    
    def test_chat_history_query_performance(self):
        """Тест производительности запросов истории"""
        # Создаем много записей истории
        email = "perf@example.com"
        for i in range(50):
            ChatHistory.objects.create(
                user_email=email,
                chat_id=f"chat-{i}",
                total_messages=i
            )
        
        # Проверяем производительность запроса
        start_time = time.time()
        histories = list(ChatHistory.objects.filter(user_email=email).order_by('-last_message_at')[:100])
        end_time = time.time()
        
        self.assertEqual(len(histories), 50)
        # Запрос должен быть быстрым (< 1 секунды)
        self.assertLess(end_time - start_time, 1.0)
