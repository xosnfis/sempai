from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
from .models import ChatRequest, ChatHistory, Metric, ChatRequestMetrics, UserActivity
from .metrics_calculator import MetricsCalculator


class ChatRequestMetricsInline(admin.StackedInline):
    """Inline для отображения метрик в ChatRequest"""
    model = ChatRequestMetrics
    can_delete = False
    extra = 0
    readonly_fields = [
        'processing_time', 'llm_processing_time', 'has_action', 'action_success',
        'has_files', 'files_processed', 'files_failed', 'message_blocked',
        'response_blocked', 'context_used', 'response_length', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Временные метрики', {
            'fields': ('processing_time', 'llm_processing_time')
        }),
        ('Метрики качества', {
            'fields': ('has_action', 'action_success', 'context_used', 'response_length')
        }),
        ('Обработка файлов', {
            'fields': ('has_files', 'files_processed', 'files_failed')
        }),
        ('Модерация', {
            'fields': ('message_blocked', 'response_blocked')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ChatRequest)
class ChatRequestAdmin(admin.ModelAdmin):
    """Админ-панель для запросов к AI"""
    
    list_display = [
        'id_short', 'status_badge', 'message_preview', 'has_response', 
        'has_action', 'created_at', 'processing_time_display'
    ]
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['id', 'message', 'response']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'completed_at', 
        'message_preview_field', 'response_preview_field', 
        'action_display', 'error_display', 'user_data_display',
        'files_data_display', 'chat_history_display', 'metrics_link'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 25
    inlines = [ChatRequestMetricsInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'status', 'created_at', 'updated_at', 'completed_at')
        }),
        ('Запрос', {
            'fields': ('message_preview_field', 'message', 'chat_history_display', 'chat_history')
        }),
        ('Ответ', {
            'fields': ('response_preview_field', 'response', 'action_display', 'action', 'error_display', 'error')
        }),
        ('Данные пользователя', {
            'fields': ('user_data_display', 'user_data', 'files_data_display', 'files_data'),
            'classes': ('collapse',)
        }),
        ('Метрики', {
            'fields': ('metrics_link',),
            'classes': ('collapse',)
        }),
    )
    
    def id_short(self, obj):
        """Короткий ID для отображения в списке"""
        return str(obj.id)[:8] + '...'
    id_short.short_description = 'ID'
    
    def status_badge(self, obj):
        """Отображение статуса с цветом"""
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    def message_preview(self, obj):
        """Превью сообщения"""
        if obj.message:
            preview = obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
            return preview
        return '-'
    message_preview.short_description = 'Сообщение'
    
    def has_response(self, obj):
        """Есть ли ответ"""
        return bool(obj.response)
    has_response.short_description = 'Ответ'
    has_response.boolean = True
    
    def has_action(self, obj):
        """Есть ли действие"""
        return bool(obj.action and obj.action != {})
    has_action.short_description = 'Действие'
    has_action.boolean = True
    
    def processing_time_display(self, obj):
        """Время обработки"""
        if hasattr(obj, 'metrics') and obj.metrics.processing_time:
            return f"{obj.metrics.processing_time:.2f} сек"
        return '-'
    processing_time_display.short_description = 'Время обработки'
    
    def message_preview_field(self, obj):
        """Превью сообщения в форме"""
        if obj.message:
            return format_html('<div style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f5f5f5; border-radius: 5px;">{}</div>', obj.message)
        return '-'
    message_preview_field.short_description = 'Превью сообщения'
    
    def response_preview_field(self, obj):
        """Превью ответа в форме"""
        if obj.response:
            return format_html('<div style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f5f5f5; border-radius: 5px;">{}</div>', obj.response)
        return '-'
    response_preview_field.short_description = 'Превью ответа'
    
    def action_display(self, obj):
        """Отображение действия"""
        if obj.action and obj.action != {}:
            action_json = json.dumps(obj.action, ensure_ascii=False, indent=2)
            return format_html(
                '<pre style="max-height: 200px; overflow-y: auto; padding: 10px; background: #e8f4f8; border-radius: 5px; font-size: 12px;">{}</pre>',
                action_json
            )
        return '-'
    action_display.short_description = 'Действие (JSON)'
    
    def error_display(self, obj):
        """Отображение ошибки"""
        if obj.error:
            return format_html(
                '<div style="max-height: 200px; overflow-y: auto; padding: 10px; background: #ffe8e8; border-radius: 5px; color: #d00;">{}</div>',
                obj.error
            )
        return '-'
    error_display.short_description = 'Ошибка'
    
    def user_data_display(self, obj):
        """Отображение данных пользователя"""
        if obj.user_data and obj.user_data != {}:
            data_json = json.dumps(obj.user_data, ensure_ascii=False, indent=2)
            return format_html(
                '<pre style="max-height: 300px; overflow-y: auto; padding: 10px; background: #f0f0f0; border-radius: 5px; font-size: 11px;">{}</pre>',
                data_json
            )
        return '-'
    user_data_display.short_description = 'Данные пользователя (JSON)'
    
    def files_data_display(self, obj):
        """Отображение данных файлов"""
        if obj.files_data and len(obj.files_data) > 0:
            files_json = json.dumps(obj.files_data, ensure_ascii=False, indent=2)
            return format_html(
                '<pre style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f0f0f0; border-radius: 5px; font-size: 11px;">{}</pre>',
                files_json
            )
        return '-'
    files_data_display.short_description = 'Файлы (JSON)'
    
    def chat_history_display(self, obj):
        """Отображение истории чата"""
        if obj.chat_history and len(obj.chat_history) > 0:
            history_json = json.dumps(obj.chat_history, ensure_ascii=False, indent=2)
            return format_html(
                '<pre style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f0f0f0; border-radius: 5px; font-size: 11px;">{}</pre>',
                history_json
            )
        return '-'
    chat_history_display.short_description = 'История чата (JSON)'
    
    def metrics_link(self, obj):
        """Ссылка на метрики"""
        if hasattr(obj, 'metrics'):
            url = reverse('admin:main_chatrequestmetrics_change', args=[obj.metrics.pk])
            return format_html('<a href="{}">Просмотреть метрики</a>', url)
        return 'Метрики еще не созданы'
    metrics_link.short_description = 'Метрики'


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    """Админ-панель для истории чатов"""
    
    list_display = [
        'chat_id_short', 'user_email', 'title', 'total_messages_badge',
        'total_actions', 'last_message_at', 'created_at'
    ]
    list_filter = ['created_at', 'last_message_at', 'total_messages']
    search_fields = ['chat_id', 'user_email', 'title']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'messages_display',
        'ai_actions_display', 'statistics_display'
    ]
    date_hierarchy = 'last_message_at'
    list_per_page = 25
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'chat_id', 'user_email', 'title')
        }),
        ('Статистика', {
            'fields': ('statistics_display', 'total_messages', 'total_user_messages', 
                      'total_ai_messages', 'total_actions')
        }),
        ('Сообщения', {
            'fields': ('messages_display', 'messages'),
            'classes': ('collapse',)
        }),
        ('Действия AI', {
            'fields': ('ai_actions_display', 'ai_actions'),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at', 'last_message_at'),
            'classes': ('collapse',)
        }),
    )
    
    def chat_id_short(self, obj):
        """Короткий chat_id"""
        return obj.chat_id[:20] + '...' if len(obj.chat_id) > 20 else obj.chat_id
    chat_id_short.short_description = 'Chat ID'
    
    def total_messages_badge(self, obj):
        """Бейдж с количеством сообщений"""
        color = 'green' if obj.total_messages > 0 else 'gray'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.total_messages
        )
    total_messages_badge.short_description = 'Сообщений'
    
    def messages_display(self, obj):
        """Отображение сообщений"""
        if obj.messages and len(obj.messages) > 0:
            messages_html = '<div style="max-height: 400px; overflow-y: auto;">'
            for i, msg in enumerate(obj.messages[:10]):  # Показываем первые 10
                is_user = msg.get('isUser', False)
                text = msg.get('text', msg.get('content', ''))[:100]
                bg_color = '#e3f2fd' if is_user else '#f1f8e9'
                messages_html += format_html(
                    '<div style="padding: 8px; margin: 5px 0; background: {}; border-radius: 5px; font-size: 12px;">'
                    '<strong>{}</strong>: {}'
                    '</div>',
                    bg_color,
                    'Пользователь' if is_user else 'AI',
                    text + ('...' if len(str(text)) > 100 else '')
                )
            if len(obj.messages) > 10:
                messages_html += f'<p style="color: #666;">... и еще {len(obj.messages) - 10} сообщений</p>'
            messages_html += '</div>'
            return mark_safe(messages_html)
        return 'Нет сообщений'
    messages_display.short_description = 'Сообщения'
    
    def ai_actions_display(self, obj):
        """Отображение действий AI"""
        if obj.ai_actions and len(obj.ai_actions) > 0:
            actions_json = json.dumps(obj.ai_actions, ensure_ascii=False, indent=2)
            return format_html(
                '<pre style="max-height: 300px; overflow-y: auto; padding: 10px; background: #fff3cd; border-radius: 5px; font-size: 11px;">{}</pre>',
                actions_json
            )
        return 'Нет действий'
    ai_actions_display.short_description = 'Действия AI (JSON)'
    
    def statistics_display(self, obj):
        """Отображение статистики"""
        stats = format_html(
            '<div style="padding: 10px; background: #f0f0f0; border-radius: 5px;">'
            '<strong>Всего сообщений:</strong> {}<br>'
            '<strong>Сообщений пользователя:</strong> {}<br>'
            '<strong>Сообщений AI:</strong> {}<br>'
            '<strong>Действий:</strong> {}'
            '</div>',
            obj.total_messages,
            obj.total_user_messages,
            obj.total_ai_messages,
            obj.total_actions
        )
        return stats
    statistics_display.short_description = 'Статистика'


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    """Админ-панель для метрик"""
    
    list_display = [
        'name', 'category_badge', 'value_display', 'target_value_display',
        'unit', 'is_target_met', 'sample_size', 'calculated_at'
    ]
    list_filter = ['category', 'calculated_at', 'name', 'unit']
    search_fields = ['name', 'category']
    readonly_fields = [
        'id', 'calculated_at', 'value_display_field', 'target_value_display_field',
        'period_display', 'metadata_display', 'status_indicator'
    ]
    date_hierarchy = 'calculated_at'
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'name', 'category', 'unit')
        }),
        ('Значения', {
            'fields': ('value_display_field', 'value', 'target_value_display_field', 'target_value', 'status_indicator')
        }),
        ('Период расчета', {
            'fields': ('period_display', 'period_start', 'period_end', 'sample_size')
        }),
        ('Метаданные', {
            'fields': ('metadata_display', 'metadata', 'calculated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def category_badge(self, obj):
        """Бейдж категории"""
        colors = {
            'response_quality': '#2196F3',
            'action_performance': '#4CAF50',
            'performance': '#FF9800',
            'reliability': '#9C27B0',
            'security': '#F44336',
            'user_experience': '#00BCD4',
            'file_processing': '#795548',
            'data_accuracy': '#607D8B',
            'calendar': '#E91E63',
            'formatting': '#9E9E9E',
            'user_engagement': '#FF5722',
            'request_analysis': '#3F51B5',
            'usage_patterns': '#009688',
            'feature_usage': '#CDDC39',
            'content_analysis': '#FFC107',
            'multimodal': '#E91E63',
            'satisfaction': '#9C27B0',
        }
        color = colors.get(obj.category, '#9E9E9E')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Категория'
    
    def value_display(self, obj):
        """Отображение значения с форматированием"""
        if obj.value is None:
            return '-'
        
        try:
            if obj.unit == 'percent':
                return f"{float(obj.value):.2f}%"
            elif obj.unit == 'seconds':
                return f"{float(obj.value):.2f} сек"
            elif obj.unit == 'requests_per_minute':
                return f"{float(obj.value):.2f} запр/мин"
            return str(obj.value)
        except (TypeError, ValueError):
            return str(obj.value) if obj.value is not None else '-'
    value_display.short_description = 'Значение'
    
    def value_display_field(self, obj):
        """Отображение значения в форме"""
        value_str = self.value_display(obj)
        return format_html(
            '<div style="padding: 10px; background: #e3f2fd; border-radius: 5px; font-size: 18px; font-weight: bold;">{}</div>',
            value_str
        )
    value_display_field.short_description = 'Текущее значение'
    
    def target_value_display(self, obj):
        """Отображение целевого значения"""
        if obj.target_value is not None:
            if obj.unit == 'percent':
                return f"{obj.target_value:.2f}%"
            elif obj.unit == 'seconds':
                return f"{obj.target_value:.2f} сек"
            elif obj.unit == 'requests_per_minute':
                return f"{obj.target_value:.2f} запр/мин"
            return str(obj.target_value)
        return 'Не задано'
    target_value_display.short_description = 'Целевое значение'
    
    def target_value_display_field(self, obj):
        """Отображение целевого значения в форме"""
        target_str = self.target_value_display(obj)
        color = '#c8e6c9' if obj.is_target_met else '#ffcdd2' if obj.target_value else '#f5f5f5'
        return format_html(
            '<div style="padding: 10px; background: {}; border-radius: 5px; font-size: 16px;">{}</div>',
            color,
            target_str
        )
    target_value_display_field.short_description = 'Целевое значение'
    
    def is_target_met(self, obj):
        """Достигнута ли цель"""
        result = obj.is_target_met
        if result is None:
            return format_html('<span style="color: gray;">N/A</span>')
        if result:
            return format_html('<span style="color: green; font-weight: bold;">✓ ДА</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ НЕТ</span>')
    is_target_met.short_description = 'Цель достигнута'
    
    def period_display(self, obj):
        """Отображение периода"""
        return format_html(
            '<div style="padding: 8px; background: #f5f5f5; border-radius: 5px;">'
            '<strong>С:</strong> {}<br>'
            '<strong>По:</strong> {}'
            '</div>',
            obj.period_start.strftime('%d.%m.%Y %H:%M'),
            obj.period_end.strftime('%d.%m.%Y %H:%M')
        )
    period_display.short_description = 'Период'
    
    def metadata_display(self, obj):
        """Отображение метаданных"""
        if obj.metadata and obj.metadata != {}:
            metadata_json = json.dumps(obj.metadata, ensure_ascii=False, indent=2)
            return format_html(
                '<pre style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f0f0f0; border-radius: 5px; font-size: 11px;">{}</pre>',
                metadata_json
            )
        return '-'
    metadata_display.short_description = 'Метаданные (JSON)'
    
    def status_indicator(self, obj):
        """Индикатор статуса"""
        result = obj.is_target_met
        if result is None:
            return format_html(
                '<div style="padding: 10px; background: #e0e0e0; border-radius: 5px; text-align: center;">'
                '<span style="font-size: 24px;">—</span><br>'
                '<small>Целевое значение не задано</small>'
                '</div>'
            )
        if result:
            return format_html(
                '<div style="padding: 10px; background: #c8e6c9; border-radius: 5px; text-align: center;">'
                '<span style="font-size: 32px; color: green;">✓</span><br>'
                '<small>Цель достигнута</small>'
                '</div>'
            )
        return format_html(
            '<div style="padding: 10px; background: #ffcdd2; border-radius: 5px; text-align: center;">'
            '<span style="font-size: 32px; color: red;">✗</span><br>'
            '<small>Цель не достигнута</small>'
            '</div>'
        )
    status_indicator.short_description = 'Статус'


@admin.register(ChatRequestMetrics)
class ChatRequestMetricsAdmin(admin.ModelAdmin):
    """Админ-панель для метрик запросов"""
    
    list_display = [
        'chat_request_link', 'processing_time_display', 'llm_time_display',
        'has_action_badge', 'action_success_badge', 'files_info', 'created_at'
    ]
    list_filter = [
        'has_action', 'action_success', 'message_blocked', 'response_blocked',
        'context_used', 'has_files', 'created_at'
    ]
    search_fields = ['chat_request__id']
    readonly_fields = [
        'chat_request_link', 'created_at', 'updated_at',
        'performance_display', 'quality_display', 'files_display',
        'moderation_display', 'context_display', 'metadata_display'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        ('Связанный запрос', {
            'fields': ('chat_request_link', 'chat_request')
        }),
        ('Производительность', {
            'fields': ('performance_display', 'processing_time', 'llm_processing_time')
        }),
        ('Качество', {
            'fields': ('quality_display', 'has_action', 'action_success', 'context_used', 'response_length')
        }),
        ('Обработка файлов', {
            'fields': ('files_display', 'has_files', 'files_processed', 'files_failed')
        }),
        ('Модерация', {
            'fields': ('moderation_display', 'message_blocked', 'response_blocked')
        }),
        ('Метаданные', {
            'fields': ('metadata_display', 'metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def chat_request_link(self, obj):
        """Ссылка на запрос"""
        url = reverse('admin:main_chatrequest_change', args=[obj.chat_request.pk])
        return format_html('<a href="{}">{}</a>', url, str(obj.chat_request.id)[:20])
    chat_request_link.short_description = 'Запрос'
    
    def processing_time_display(self, obj):
        """Время обработки"""
        if obj.processing_time is not None:
            try:
                time_value = float(obj.processing_time)
                color = 'green' if time_value < 5 else 'orange' if time_value < 10 else 'red'
                time_str = f"{time_value:.2f} сек"
                return format_html(
                    '<span style="color: {}; font-weight: bold;">{}</span>',
                    color,
                    time_str
                )
            except (TypeError, ValueError):
                return str(obj.processing_time)
        return '-'
    processing_time_display.short_description = 'Время обработки'
    
    def llm_time_display(self, obj):
        """Время LLM"""
        if obj.llm_processing_time is not None:
            try:
                time_value = float(obj.llm_processing_time)
                time_str = f"{time_value:.2f} сек"
                return format_html('<span>{}</span>', time_str)
            except (TypeError, ValueError):
                return str(obj.llm_processing_time)
        return '-'
    llm_time_display.short_description = 'Время LLM'
    
    def has_action_badge(self, obj):
        """Бейдж наличия действия"""
        if obj.has_action:
            return format_html('<span style="background-color: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px;">✓</span>')
        return format_html('<span style="color: gray;">—</span>')
    has_action_badge.short_description = 'Действие'
    
    def action_success_badge(self, obj):
        """Бейдж успешности действия"""
        if obj.action_success is None:
            return format_html('<span style="color: gray;">—</span>')
        if obj.action_success:
            return format_html('<span style="background-color: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px;">✓</span>')
        return format_html('<span style="background-color: #F44336; color: white; padding: 3px 8px; border-radius: 3px;">✗</span>')
    action_success_badge.short_description = 'Успех действия'
    
    def files_info(self, obj):
        """Информация о файлах"""
        if obj.has_files:
            return format_html(
                '<span style="background-color: #2196F3; color: white; padding: 3px 8px; border-radius: 3px;">'
                '{} / {}'
                '</span>',
                obj.files_processed,
                obj.files_processed + obj.files_failed
            )
        return '-'
    files_info.short_description = 'Файлы'
    
    def performance_display(self, obj):
        """Отображение производительности"""
        html = '<div style="padding: 10px; background: #e3f2fd; border-radius: 5px;">'
        if obj.processing_time is not None:
            try:
                time_value = float(obj.processing_time)
                html += f'<strong>Общее время:</strong> {time_value:.2f} сек<br>'
            except (TypeError, ValueError):
                html += f'<strong>Общее время:</strong> {obj.processing_time}<br>'
        if obj.llm_processing_time is not None:
            try:
                llm_value = float(obj.llm_processing_time)
                html += f'<strong>Время LLM:</strong> {llm_value:.2f} сек<br>'
            except (TypeError, ValueError):
                html += f'<strong>Время LLM:</strong> {obj.llm_processing_time}<br>'
        if obj.processing_time is not None and obj.llm_processing_time is not None:
            try:
                proc_time = float(obj.processing_time)
                llm_time = float(obj.llm_processing_time)
                other_time = proc_time - llm_time
                html += f'<strong>Другое:</strong> {other_time:.2f} сек'
            except (TypeError, ValueError):
                pass
        html += '</div>'
        return mark_safe(html)
    performance_display.short_description = 'Производительность'
    
    def quality_display(self, obj):
        """Отображение качества"""
        html = '<div style="padding: 10px; background: #f1f8e9; border-radius: 5px;">'
        html += f'<strong>Действие:</strong> {"✓" if obj.has_action else "✗"}<br>'
        if obj.action_success is not None:
            html += f'<strong>Успех:</strong> {"✓" if obj.action_success else "✗"}<br>'
        html += f'<strong>Контекст:</strong> {"✓" if obj.context_used else "✗"}<br>'
        html += f'<strong>Длина ответа:</strong> {obj.response_length} символов'
        html += '</div>'
        return mark_safe(html)
    quality_display.short_description = 'Качество'
    
    def files_display(self, obj):
        """Отображение файлов"""
        if obj.has_files:
            html = '<div style="padding: 10px; background: #fff3cd; border-radius: 5px;">'
            html += f'<strong>Обработано:</strong> {obj.files_processed}<br>'
            html += f'<strong>Ошибок:</strong> {obj.files_failed}<br>'
            html += f'<strong>Всего:</strong> {obj.files_processed + obj.files_failed}'
            html += '</div>'
            return mark_safe(html)
        return 'Файлов нет'
    files_display.short_description = 'Файлы'
    
    def moderation_display(self, obj):
        """Отображение модерации"""
        html = '<div style="padding: 10px; background: #ffebee; border-radius: 5px;">'
        html += f'<strong>Сообщение заблокировано:</strong> {"✓" if obj.message_blocked else "✗"}<br>'
        html += f'<strong>Ответ заблокирован:</strong> {"✓" if obj.response_blocked else "✗"}'
        html += '</div>'
        return mark_safe(html)
    moderation_display.short_description = 'Модерация'
    
    def context_display(self, obj):
        """Отображение использования контекста"""
        if obj.context_used:
            return format_html(
                '<div style="padding: 10px; background: #c8e6c9; border-radius: 5px; text-align: center;">'
                '<span style="font-size: 24px; color: green;">✓</span><br>'
                '<small>Контекст использован</small>'
                '</div>'
            )
        return format_html(
            '<div style="padding: 10px; background: #ffcdd2; border-radius: 5px; text-align: center;">'
            '<span style="font-size: 24px; color: red;">✗</span><br>'
            '<small>Контекст не использован</small>'
            '</div>'
        )
    context_display.short_description = 'Использование контекста'
    
    def metadata_display(self, obj):
        """Отображение метаданных"""
        if obj.metadata and obj.metadata != {}:
            metadata_json = json.dumps(obj.metadata, ensure_ascii=False, indent=2)
            return format_html(
                '<pre style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f0f0f0; border-radius: 5px; font-size: 11px;">{}</pre>',
                metadata_json
            )
        return '-'
    metadata_display.short_description = 'Метаданные (JSON)'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Админ-панель для активности пользователей"""
    
    list_display = [
        'activity_type_badge', 'user_email_display', 'user_link', 'created_at', 
        'chat_request_link', 'ip_address'
    ]
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user_email', 'user__email', 'user__username', 'activity_data']
    readonly_fields = [
        'id', 'created_at', 'user_link', 'activity_data_display', 
        'chat_request_link', 'user_agent_display'
    ]
    date_hierarchy = 'created_at'
    list_per_page = 50
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'activity_type', 'user_link', 'user', 'user_email', 'created_at')
        }),
        ('Связанные объекты', {
            'fields': ('chat_request_link', 'chat_request')
        }),
        ('Данные активности', {
            'fields': ('activity_data_display', 'activity_data')
        }),
        ('Техническая информация', {
            'fields': ('ip_address', 'user_agent_display', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def activity_type_badge(self, obj):
        """Бейдж типа активности"""
        colors = {
            'registration': '#4CAF50',
            'login': '#2196F3',
            'chat_request': '#FF9800',
            'page_view': '#9C27B0',
            'feature_use': '#00BCD4',
            'file_upload': '#795548',
            'calendar_action': '#E91E63',
            'document_action': '#607D8B',
            'other': '#9E9E9E',
        }
        color = colors.get(obj.activity_type, '#9E9E9E')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_activity_type_display()
        )
    activity_type_badge.short_description = 'Тип активности'
    
    def user_email_display(self, obj):
        """Отображение email пользователя"""
        email = obj.effective_user_email
        if email:
            return email
        return '-'
    user_email_display.short_description = 'Email'
    
    def user_link(self, obj):
        """Ссылка на пользователя"""
        if obj.user:
            from django.contrib.auth.models import User
            url = reverse('admin:auth_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.email)
        return '-'
    user_link.short_description = 'Пользователь'
    
    def chat_request_link(self, obj):
        """Ссылка на запрос"""
        if obj.chat_request:
            url = reverse('admin:main_chatrequest_change', args=[obj.chat_request.pk])
            return format_html('<a href="{}">{}</a>', url, str(obj.chat_request.id)[:20])
        return '-'
    chat_request_link.short_description = 'Запрос'
    
    def activity_data_display(self, obj):
        """Отображение данных активности"""
        if obj.activity_data and obj.activity_data != {}:
            data_json = json.dumps(obj.activity_data, ensure_ascii=False, indent=2)
            return format_html(
                '<pre style="max-height: 200px; overflow-y: auto; padding: 10px; background: #f0f0f0; border-radius: 5px; font-size: 11px;">{}</pre>',
                data_json
            )
        return '-'
    activity_data_display.short_description = 'Данные активности (JSON)'
    
    def user_agent_display(self, obj):
        """Отображение User-Agent"""
        if obj.user_agent:
            return format_html(
                '<div style="max-height: 100px; overflow-y: auto; padding: 8px; background: #f5f5f5; border-radius: 5px; font-size: 11px;">{}</div>',
                obj.user_agent
            )
        return '-'
    user_agent_display.short_description = 'User-Agent'


# Кастомная страница для отображения сводки метрик в админ-панели
def metrics_summary_view(request):
    """Кастомная страница для отображения сводки метрик в админ-панели"""
    from django.contrib.auth.decorators import user_passes_test
    
    # Проверяем права доступа
    if not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    try:
        # Параметры
        days = int(request.GET.get('days', 7))
        period_end = timezone.now()
        period_start = period_end - timedelta(days=days)
        
        # Рассчитываем метрики, если их еще нет
        # Используем более гибкий фильтр - метрики, которые пересекаются с периодом
        recent_metrics = Metric.objects.filter(
            period_start__lte=period_end,
            period_end__gte=period_start
        ).exists()
        
        if not recent_metrics:
            # Автоматически рассчитываем метрики
            MetricsCalculator.calculate_all_metrics(period_start, period_end)
        
        # Получаем последние значения метрик по категориям
        summary = {}
        
        for category_code, category_name in Metric.METRIC_CATEGORIES:
            # Получаем уникальные метрики (последнее значение для каждой)
            # Сначала пытаемся найти метрики, пересекающиеся с периодом
            all_category_metrics = Metric.objects.filter(
                category=category_code,
                period_start__lte=period_end,
                period_end__gte=period_start
            ).order_by('name', '-calculated_at')
            
            # Если не нашли метрики для периода, берем последние метрики независимо от периода
            if not all_category_metrics.exists():
                all_category_metrics = Metric.objects.filter(
                    category=category_code
                ).order_by('name', '-calculated_at')
            
            # Фильтруем, оставляя только последнее значение для каждой метрики
            seen_names = set()
            category_metrics = []
            for metric in all_category_metrics:
                if metric.name not in seen_names:
                    seen_names.add(metric.name)
                    category_metrics.append(metric)
            
            category_data = []
            for metric in category_metrics:
                category_data.append({
                    'name': metric.name,
                    'value': metric.value,
                    'target_value': metric.target_value,
                    'unit': metric.unit,
                    'is_target_met': metric.is_target_met,
                    'sample_size': metric.sample_size
                })
            
            if category_data:
                summary[category_code] = {
                    'name': category_name,
                    'metrics': category_data
                }
        
        # Общая статистика (используем более гибкий фильтр)
        # Если запросов в периоде нет, показываем все запросы за последние 30 дней
        total_requests = ChatRequest.objects.filter(
            created_at__gte=period_start,
            created_at__lte=period_end
        ).count()
        
        # Fallback: если в периоде нет запросов, расширяем период
        if total_requests == 0:
            extended_period_start = period_end - timedelta(days=30)
            total_requests = ChatRequest.objects.filter(
                created_at__gte=extended_period_start,
                created_at__lte=period_end
            ).count()
            completed_requests = ChatRequest.objects.filter(
                created_at__gte=extended_period_start,
                created_at__lte=period_end,
                status=ChatRequest.STATUS_COMPLETED
            ).count()
            failed_requests = ChatRequest.objects.filter(
                created_at__gte=extended_period_start,
                created_at__lte=period_end,
                status=ChatRequest.STATUS_FAILED
            ).count()
        else:
            completed_requests = ChatRequest.objects.filter(
                created_at__gte=period_start,
                created_at__lte=period_end,
                status=ChatRequest.STATUS_COMPLETED
            ).count()
            
            failed_requests = ChatRequest.objects.filter(
                created_at__gte=period_start,
                created_at__lte=period_end,
                status=ChatRequest.STATUS_FAILED
            ).count()
        
        success_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
        
        context = {
            'summary': summary,
            'statistics': {
                'total_requests': total_requests,
                'completed_requests': completed_requests,
                'failed_requests': failed_requests,
                'success_rate': success_rate
            },
            'period': {
                'start': period_start,
                'end': period_end,
                'days': days
            },
            'title': 'Сводка метрик',
            'opts': Metric._meta,
            'has_view_permission': True,
        }
        
        return render(request, 'admin/metrics_summary.html', context)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка при получении сводки метрик: {str(e)}", exc_info=True)
        context = {
            'error': str(e),
            'title': 'Ошибка загрузки метрик',
            'opts': Metric._meta,
        }
        return render(request, 'admin/metrics_summary_error.html', context, status=500)


# Расширяем AdminSite для добавления кастомного URL
class CustomAdminSite(admin.AdminSite):
    """Кастомный AdminSite с дополнительными страницами"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('main/metrics/summary/', self.admin_view(metrics_summary_view), name='main_metrics_summary'),
        ]
        return custom_urls + urls


# Используем стандартный admin site, но добавляем кастомный URL через get_urls
# Переопределяем get_urls для MetricAdmin
original_get_urls = admin.site.get_urls

def custom_get_urls():
    """Добавляем кастомный URL для метрик"""
    urls = original_get_urls()
    custom_urls = [
        path('main/metrics/summary/', admin.site.admin_view(metrics_summary_view), name='main_metrics_summary'),
    ]
    return custom_urls + urls

admin.site.get_urls = custom_get_urls
