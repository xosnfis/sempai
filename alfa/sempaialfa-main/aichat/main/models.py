from django.db import models
import uuid
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class ChatRequest(models.Model):
    """Модель для хранения запросов к AI и их статусов"""
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Ожидает обработки'),
        (STATUS_PROCESSING, 'Обрабатывается'),
        (STATUS_COMPLETED, 'Завершено'),
        (STATUS_FAILED, 'Ошибка'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    message = models.TextField(blank=True)
    chat_history = models.JSONField(default=list, blank=True)
    user_data = models.JSONField(default=dict, blank=True)
    files_data = models.JSONField(default=list, blank=True)
    
    # Результаты
    response = models.TextField(blank=True, null=True)
    action = models.JSONField(default=dict, blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"ChatRequest {self.id} - {self.status}"


class ChatHistory(models.Model):
    """Модель для хранения истории чатов"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_email = models.EmailField(db_index=True)
    chat_id = models.CharField(max_length=255, db_index=True)  # ID чата из localStorage
    title = models.CharField(max_length=500, default='Новый чат')
    
    # История сообщений
    messages = models.JSONField(default=list)  # Список сообщений
    
    # Логирование действий AI
    ai_actions = models.JSONField(default=list)  # Список действий AI
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    # Статистика
    total_messages = models.IntegerField(default=0)
    total_user_messages = models.IntegerField(default=0)
    total_ai_messages = models.IntegerField(default=0)
    total_actions = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['user_email', '-last_message_at']),
            models.Index(fields=['chat_id']),
        ]
        verbose_name = 'История чата'
        verbose_name_plural = 'Истории чатов'
    
    def __str__(self):
        return f"ChatHistory {self.chat_id} - {self.user_email} ({self.total_messages} сообщений)"


class Metric(models.Model):
    """Модель для хранения метрик качества работы"""
    
    METRIC_CATEGORIES = [
        ('response_quality', 'Качество ответов'),
        ('action_performance', 'Выполнение действий'),
        ('performance', 'Производительность'),
        ('reliability', 'Надежность'),
        ('security', 'Безопасность'),
        ('user_experience', 'Пользовательский опыт'),
        ('file_processing', 'Обработка файлов'),
        ('data_accuracy', 'Точность данных'),
        ('calendar', 'Работа с календарем'),
        ('formatting', 'Форматирование'),
        ('user_engagement', 'Активность пользователей'),
        ('request_analysis', 'Анализ запросов'),
        ('usage_patterns', 'Паттерны использования'),
        ('feature_usage', 'Использование функций'),
        ('content_analysis', 'Анализ контента'),
        ('multimodal', 'Мультимодальность'),
        ('satisfaction', 'Удовлетворенность'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, db_index=True)  # Название метрики
    category = models.CharField(max_length=50, choices=METRIC_CATEGORIES, db_index=True)
    value = models.FloatField()  # Значение метрики
    target_value = models.FloatField(null=True, blank=True)  # Целевое значение
    unit = models.CharField(max_length=20, default='percent')  # Единица измерения
    
    # Период расчета
    period_start = models.DateTimeField(db_index=True)  # Начало периода
    period_end = models.DateTimeField(db_index=True)  # Конец периода
    
    # Метаданные
    calculated_at = models.DateTimeField(auto_now_add=True)
    sample_size = models.IntegerField(default=0)  # Размер выборки
    
    # Дополнительные данные
    metadata = models.JSONField(default=dict, blank=True)  # Дополнительная информация
    
    class Meta:
        ordering = ['-calculated_at', '-period_end']
        indexes = [
            models.Index(fields=['name', '-calculated_at']),
            models.Index(fields=['category', '-calculated_at']),
            models.Index(fields=['period_start', 'period_end']),
        ]
        verbose_name = 'Метрика'
        verbose_name_plural = 'Метрики'
    
    def __str__(self):
        return f"{self.name}: {self.value:.2f} {self.unit} ({self.period_start.date()} - {self.period_end.date()})"
    
    @property
    def is_target_met(self):
        """Проверяет, достигнуто ли целевое значение"""
        if self.target_value is None:
            return None
        return self.value >= self.target_value


class ChatRequestMetrics(models.Model):
    """Модель для хранения метрик конкретного запроса"""
    
    chat_request = models.OneToOneField(ChatRequest, on_delete=models.CASCADE, related_name='metrics')
    
    # Временные метрики
    processing_time = models.FloatField(null=True, blank=True)  # Время обработки в секундах
    llm_processing_time = models.FloatField(null=True, blank=True)  # Время обработки LLM
    
    # Метрики качества
    has_action = models.BooleanField(default=False)  # Есть ли действие в ответе
    action_success = models.BooleanField(null=True, blank=True)  # Успешно ли выполнено действие
    has_files = models.BooleanField(default=False)  # Есть ли файлы в запросе
    files_processed = models.IntegerField(default=0)  # Количество обработанных файлов
    files_failed = models.IntegerField(default=0)  # Количество необработанных файлов
    
    # Метрики модерации
    message_blocked = models.BooleanField(default=False)  # Заблокировано ли сообщение
    response_blocked = models.BooleanField(default=False)  # Заблокирован ли ответ
    
    # Метрики использования контекста
    context_used = models.BooleanField(default=False)  # Использован ли контекст пользователя
    response_length = models.IntegerField(default=0)  # Длина ответа в символах
    
    # Дополнительные метрики
    metadata = models.JSONField(default=dict, blank=True)  # Дополнительная информация
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Метрики запроса'
        verbose_name_plural = 'Метрики запросов'
        indexes = [
            models.Index(fields=['chat_request']),
        ]
    
    def __str__(self):
        return f"Metrics for {self.chat_request.id}"


class UserActivity(models.Model):
    """Модель для отслеживания действий пользователей"""
    
    ACTIVITY_TYPES = [
        ('registration', 'Регистрация'),
        ('login', 'Вход'),
        ('chat_request', 'Запрос в чат'),
        ('page_view', 'Просмотр страницы'),
        ('feature_use', 'Использование функции'),
        ('file_upload', 'Загрузка файла'),
        ('calendar_action', 'Действие с календарем'),
        ('document_action', 'Действие с документом'),
        ('other', 'Другое'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    user_email = models.EmailField(db_index=True, null=True, blank=True)  # Для случаев, когда user=None
    
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES, db_index=True)
    activity_data = models.JSONField(default=dict, blank=True)  # Дополнительные данные о действии
    
    # Связь с ChatRequest, если действие связано с запросом
    chat_request = models.ForeignKey(ChatRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='activities')
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user_email', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Активность пользователя'
        verbose_name_plural = 'Активности пользователей'
    
    def __str__(self):
        user_info = self.user.email if self.user else (self.user_email or 'Unknown')
        return f"{self.get_activity_type_display()} - {user_info} ({self.created_at.date()})"
    
    @property
    def effective_user_email(self):
        """Возвращает email пользователя из user или user_email"""
        if self.user:
            return self.user.email
        return self.user_email
