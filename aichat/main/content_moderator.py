"""
Модуль цензуры и модерации контента для LLM
Фильтрует входящие сообщения пользователя и ответы AI
"""
import re
import logging

logger = logging.getLogger(__name__)


class ContentModerator:
    """Класс для модерации контента"""
    
    # Список запрещенных слов (можно расширить)
    FORBIDDEN_WORDS = [
        # Добавьте здесь запрещенные слова
    ]
    
    # Запрещенные темы/паттерны
    FORBIDDEN_PATTERNS = [
        r'как.*взломать',
        r'как.*обмануть',
        r'как.*украсть',
        r'как.*убить',
        r'как.*взорвать',
        r'наркотик',
        r'наркота',
        r'суицид',
        r'самоубийство',
    ]
    
    # Минимальная длина сообщения (чтобы избежать спама)
    MIN_MESSAGE_LENGTH = 1
    
    # Максимальная длина сообщения
    MAX_MESSAGE_LENGTH = 10000
    
    @classmethod
    def check_message(cls, message):
        """
        Проверяет сообщение на наличие запрещенного контента
        
        Args:
            message: Текст сообщения для проверки
            
        Returns:
            dict: {
                'allowed': bool - разрешено ли сообщение,
                'reason': str - причина блокировки (если не разрешено),
                'filtered_message': str - отфильтрованное сообщение
            }
        """
        if not message or not isinstance(message, str):
            return {
                'allowed': False,
                'reason': 'Пустое или неверное сообщение',
                'filtered_message': ''
            }
        
        message_lower = message.lower().strip()
        
        # Проверка длины
        if len(message) < cls.MIN_MESSAGE_LENGTH:
            return {
                'allowed': False,
                'reason': 'Сообщение слишком короткое',
                'filtered_message': message
            }
        
        if len(message) > cls.MAX_MESSAGE_LENGTH:
            return {
                'allowed': False,
                'reason': f'Сообщение слишком длинное (максимум {cls.MAX_MESSAGE_LENGTH} символов)',
                'filtered_message': message[:cls.MAX_MESSAGE_LENGTH]
            }
        
        # Проверка на запрещенные слова
        for word in cls.FORBIDDEN_WORDS:
            if word.lower() in message_lower:
                logger.warning(f"Обнаружено запрещенное слово в сообщении: {word}")
                return {
                    'allowed': False,
                    'reason': 'Сообщение содержит недопустимый контент',
                    'filtered_message': cls._filter_message(message, word)
                }
        
        # Проверка на запрещенные паттерны
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.warning(f"Обнаружен запрещенный паттерн в сообщении: {pattern}")
                return {
                    'allowed': False,
                    'reason': 'Сообщение содержит недопустимый контент',
                    'filtered_message': message  # Не фильтруем, просто блокируем
                }
        
        # Проверка на спам (множественные повторения)
        if cls._is_spam(message):
            return {
                'allowed': False,
                'reason': 'Сообщение похоже на спам',
                'filtered_message': message
            }
        
        return {
            'allowed': True,
            'reason': None,
            'filtered_message': message
        }
    
    @classmethod
    def check_ai_response(cls, response):
        """
        Проверяет ответ AI на наличие нежелательного контента
        
        Args:
            response: Текст ответа AI
            
        Returns:
            dict: {
                'allowed': bool - разрешен ли ответ,
                'reason': str - причина блокировки,
                'filtered_response': str - отфильтрованный ответ
            }
        """
        if not response or not isinstance(response, str):
            return {
                'allowed': True,  # Разрешаем пустые ответы
                'reason': None,
                'filtered_response': response or ''
            }
        
        response_lower = response.lower()
        
        # Проверка на запрещенные слова в ответе AI
        for word in cls.FORBIDDEN_WORDS:
            if word.lower() in response_lower:
                logger.warning(f"Обнаружено запрещенное слово в ответе AI: {word}")
                return {
                    'allowed': False,
                    'reason': 'Ответ содержит недопустимый контент',
                    'filtered_response': cls._filter_message(response, word)
                }
        
        # Проверка на запрещенные паттерны
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, response_lower, re.IGNORECASE):
                logger.warning(f"Обнаружен запрещенный паттерн в ответе AI: {pattern}")
                return {
                    'allowed': False,
                    'reason': 'Ответ содержит недопустимый контент',
                    'filtered_response': 'Извините, я не могу ответить на этот запрос.'
                }
        
        return {
            'allowed': True,
            'reason': None,
            'filtered_response': response
        }
    
    @classmethod
    def _filter_message(cls, message, word):
        """Фильтрует запрещенное слово из сообщения"""
        # Заменяем запрещенное слово на звездочки
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        return pattern.sub('***', message)
    
    @classmethod
    def _is_spam(cls, message):
        """Проверяет, является ли сообщение спамом"""
        # Проверка на множественные повторения символов (например, "аааааа")
        if re.search(r'(.)\1{10,}', message):
            return True
        
        # Проверка на множественные повторения слов
        words = message.split()
        if len(words) > 5:
            word_counts = {}
            for word in words:
                word_lower = word.lower()
                word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
                if word_counts[word_lower] > len(words) * 0.5:  # Если одно слово повторяется более 50%
                    return True
        
        return False
    
    @classmethod
    def sanitize_message(cls, message):
        """
        Очищает сообщение от потенциально опасных символов
        
        Args:
            message: Исходное сообщение
            
        Returns:
            str: Очищенное сообщение
        """
        if not message:
            return ''
        
        # Удаляем управляющие символы (кроме переносов строк и табуляции)
        message = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', message)
        
        # Ограничиваем длину
        if len(message) > cls.MAX_MESSAGE_LENGTH:
            message = message[:cls.MAX_MESSAGE_LENGTH]
        
        return message.strip()

