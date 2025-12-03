"""
Модуль для расчета метрик качества работы модели
"""
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Count, Avg, Sum, F, FloatField, Case, When, IntegerField, Exists, OuterRef
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from .models import ChatRequest, ChatRequestMetrics, Metric, ChatHistory
from .content_moderator import ContentModerator

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Класс для расчета метрик качества работы модели"""
    
    # Целевые значения метрик
    TARGET_VALUES = {
        'response_relevance': 85.0,
        'information_accuracy': 90.0,
        'business_style_compliance': 95.0,
        'response_completeness': 80.0,
        'action_success_rate': 90.0,
        'parameter_extraction_accuracy': 85.0,
        'command_recognition_rate': 95.0,
        'response_time_p50': 5.0,
        'response_time_p95': 10.0,
        'llm_processing_time_p50': 3.0,
        'throughput': 10.0,
        'request_success_rate': 95.0,
        'error_rate': 5.0,
        'service_availability': 99.0,
        'content_moderation_effectiveness': 98.0,
        'false_positive_rate': 2.0,
        'ai_response_blocking_rate': 1.0,
        'task_completion_rate': 85.0,
        'clarification_rate': 10.0,
        'file_processing_success_rate': 90.0,
        'format_support_rate': 95.0,
        'data_extraction_accuracy': 90.0,
        'context_utilization_rate': 80.0,
        'event_creation_accuracy': 95.0,
        'event_update_accuracy': 90.0,
        'table_formatting_accuracy': 95.0,
        'chart_command_accuracy': 90.0,
        'user_activity_rate': 5.0,  # запросов на пользователя
        'user_retention_rate_7d': 60.0,  # процент через 7 дней
        'user_retention_rate_30d': 40.0,  # процент через 30 дней
        # Метрики длины запросов/ответов
        'avg_request_length': 100.0,  # символов
        'avg_response_length': 500.0,  # символов
        'request_response_ratio': 4.0,  # соотношение
        'long_request_rate': 20.0,  # процент
        # Метрики использования истории чата
        'chat_history_usage_rate': 60.0,  # процент
        'avg_chat_history_length': 5.0,  # сообщений
        'multi_turn_conversation_rate': 40.0,  # процент
        # Метрики времени и паттернов
        'peak_hours_activity': 30.0,  # процент
        'weekend_activity_rate': 20.0,  # процент
        'avg_requests_per_session': 4.0,  # запросов
        # Метрики повторных запросов и ошибок
        'retry_rate': 10.0,  # процент
        'error_recovery_rate': 80.0,  # процент
        'timeout_rate': 2.0,  # процент
        'connection_error_rate': 1.0,  # процент
        # Метрики конверсии действий
        'action_conversion_rate': 30.0,  # процент
        'action_attempt_rate': 35.0,  # процент
        'action_failure_rate': 10.0,  # процент
        'avg_actions_per_request': 1.0,  # действий
        # Метрики использования функций
        'file_attachment_rate': 15.0,  # процент
        'calendar_action_rate': 20.0,  # процент
        'multi_feature_usage_rate': 5.0,  # процент
        'feature_combination_rate': 2.0,  # процент
        # Метрики качества контекста
        'context_completeness_rate': 70.0,  # процент
        'context_utilization_effectiveness': 85.0,  # процент
        'missing_context_rate': 20.0,  # процент
        # Метрики сессий
        'avg_session_duration': 10.0,  # минут
        'avg_time_between_requests': 30.0,  # секунд
        'session_completion_rate': 60.0,  # процент
        'returning_user_rate': 50.0,  # процент
        # Метрики популярных запросов
        'unique_request_rate': 70.0,  # процент
        'repeated_request_rate': 30.0,  # процент
        # Метрики мультимодальности
        'image_processing_rate': 5.0,  # процент
        'image_processing_success_rate': 90.0,  # процент
        'multimodal_request_rate': 10.0,  # процент
        # Метрики производительности по типам
        'action_request_processing_time': 8.0,  # секунд
        'file_request_processing_time': 12.0,  # секунд
        'simple_request_processing_time': 3.0,  # секунд
    }
    
    @classmethod
    def calculate_all_metrics(cls, period_start=None, period_end=None):
        """
        Рассчитывает все метрики за указанный период
        
        Args:
            period_start: Начало периода (по умолчанию - последние 7 дней)
            period_end: Конец периода (по умолчанию - сейчас)
        """
        if period_end is None:
            period_end = timezone.now()
        if period_start is None:
            period_start = period_end - timedelta(days=7)
        
        logger.info(f"Расчет метрик за период: {period_start} - {period_end}")
        
        # Фильтр для запросов за период
        requests_filter = Q(created_at__gte=period_start, created_at__lte=period_end)
        
        metrics = []
        
        # 1. Метрики качества ответов
        metrics.extend(cls._calculate_response_quality_metrics(requests_filter, period_start, period_end))
        
        # 2. Метрики выполнения действий
        metrics.extend(cls._calculate_action_metrics(requests_filter, period_start, period_end))
        
        # 3. Метрики производительности
        metrics.extend(cls._calculate_performance_metrics(requests_filter, period_start, period_end))
        
        # 4. Метрики надежности
        metrics.extend(cls._calculate_reliability_metrics(requests_filter, period_start, period_end))
        
        # 5. Метрики безопасности
        metrics.extend(cls._calculate_security_metrics(requests_filter, period_start, period_end))
        
        # 6. Метрики пользовательского опыта
        metrics.extend(cls._calculate_user_experience_metrics(requests_filter, period_start, period_end))
        
        # 7. Метрики обработки файлов
        metrics.extend(cls._calculate_file_processing_metrics(requests_filter, period_start, period_end))
        
        # 8. Метрики работы с данными
        metrics.extend(cls._calculate_data_accuracy_metrics(requests_filter, period_start, period_end))
        
        # 9. Метрики работы с календарем
        metrics.extend(cls._calculate_calendar_metrics(requests_filter, period_start, period_end))
        
        # 10. Метрики форматирования
        metrics.extend(cls._calculate_formatting_metrics(requests_filter, period_start, period_end))
        
        # 11. Метрики активности пользователей
        metrics.extend(cls._calculate_user_engagement_metrics(requests_filter, period_start, period_end))
        
        # 12. Метрики длины запросов/ответов
        metrics.extend(cls._calculate_request_length_metrics(requests_filter, period_start, period_end))
        
        # 13. Метрики использования истории чата
        metrics.extend(cls._calculate_chat_history_metrics(requests_filter, period_start, period_end))
        
        # 14. Метрики паттернов использования
        metrics.extend(cls._calculate_usage_patterns_metrics(requests_filter, period_start, period_end))
        
        # 15. Метрики ошибок и повторных запросов
        metrics.extend(cls._calculate_error_metrics(requests_filter, period_start, period_end))
        
        # 16. Метрики конверсии действий
        metrics.extend(cls._calculate_action_conversion_metrics(requests_filter, period_start, period_end))
        
        # 17. Метрики использования функций
        metrics.extend(cls._calculate_feature_usage_metrics(requests_filter, period_start, period_end))
        
        # 18. Метрики качества контекста
        metrics.extend(cls._calculate_context_quality_metrics(requests_filter, period_start, period_end))
        
        # 19. Метрики сессий пользователей
        metrics.extend(cls._calculate_session_metrics(requests_filter, period_start, period_end))
        
        # 20. Метрики анализа контента
        metrics.extend(cls._calculate_content_analysis_metrics(requests_filter, period_start, period_end))
        
        # 21. Метрики мультимодальности
        metrics.extend(cls._calculate_multimodal_metrics(requests_filter, period_start, period_end))
        
        # 22. Метрики производительности по типам
        metrics.extend(cls._calculate_performance_by_type_metrics(requests_filter, period_start, period_end))
        
        # Сохраняем все метрики
        for metric_data in metrics:
            Metric.objects.create(**metric_data)
        
        logger.info(f"Рассчитано {len(metrics)} метрик")
        return metrics
    
    @classmethod
    def _calculate_response_quality_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик качества ответов"""
        metrics = []
        
        # Получаем запросы с метриками
        requests_with_metrics = ChatRequest.objects.filter(
            requests_filter,
            metrics__isnull=False
        ).select_related('metrics')
        
        total_requests = requests_with_metrics.count()
        if total_requests == 0:
            return metrics
        
        # Response Completeness - полнота ответа (наличие ответа)
        completed_with_response = requests_with_metrics.filter(
            status=ChatRequest.STATUS_COMPLETED,
            response__isnull=False
        ).exclude(response='').count()
        
        response_completeness = (completed_with_response / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'response_completeness',
            'category': 'response_quality',
            'value': response_completeness,
            'target_value': cls.TARGET_VALUES.get('response_completeness'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'completed_with_response': completed_with_response,
                'total_requests': total_requests
            }
        })
        
        # Business Style Compliance - проверка делового стиля (упрощенная)
        # Считаем, что если ответ не заблокирован модератором, то стиль приемлемый
        non_blocked_responses = requests_with_metrics.filter(
            metrics__response_blocked=False
        ).count()
        
        business_style_compliance = (non_blocked_responses / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'business_style_compliance',
            'category': 'response_quality',
            'value': business_style_compliance,
            'target_value': cls.TARGET_VALUES.get('business_style_compliance'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'non_blocked_responses': non_blocked_responses
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_action_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик выполнения действий"""
        metrics = []
        
        requests_with_metrics = ChatRequest.objects.filter(
            requests_filter,
            metrics__isnull=False
        ).select_related('metrics')
        
        # Action Success Rate
        requests_with_actions = requests_with_metrics.filter(metrics__has_action=True)
        total_actions = requests_with_actions.count()
        
        if total_actions > 0:
            successful_actions = requests_with_actions.filter(metrics__action_success=True).count()
            action_success_rate = (successful_actions / total_actions * 100)
            
            metrics.append({
                'name': 'action_success_rate',
                'category': 'action_performance',
                'value': action_success_rate,
                'target_value': cls.TARGET_VALUES.get('action_success_rate'),
                'unit': 'percent',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': total_actions,
                'metadata': {
                    'successful_actions': successful_actions,
                    'total_actions': total_actions
                }
            })
        
        # Command Recognition Rate
        # Считаем запросы, где есть действие в ответе
        total_requests = requests_with_metrics.count()
        if total_requests > 0:
            recognized_commands = requests_with_metrics.filter(
                Q(action__isnull=False) | Q(metrics__has_action=True)
            ).count()
            
            command_recognition_rate = (recognized_commands / total_requests * 100)
            
            metrics.append({
                'name': 'command_recognition_rate',
                'category': 'action_performance',
                'value': command_recognition_rate,
                'target_value': cls.TARGET_VALUES.get('command_recognition_rate'),
                'unit': 'percent',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': total_requests,
                'metadata': {
                    'recognized_commands': recognized_commands
                }
            })
        
        return metrics
    
    @classmethod
    def _calculate_performance_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик производительности"""
        metrics = []
        
        requests_with_metrics = ChatRequest.objects.filter(
            requests_filter,
            metrics__isnull=False,
            metrics__processing_time__isnull=False
        ).select_related('metrics')
        
        total_requests = requests_with_metrics.count()
        if total_requests == 0:
            return metrics
        
        # Response Time (p50 и p95)
        processing_times = list(
            requests_with_metrics.values_list('metrics__processing_time', flat=True)
        )
        processing_times.sort()
        
        if processing_times:
            p50_index = int(len(processing_times) * 0.5)
            p95_index = int(len(processing_times) * 0.95)
            
            response_time_p50 = processing_times[p50_index] if p50_index < len(processing_times) else processing_times[-1]
            response_time_p95 = processing_times[p95_index] if p95_index < len(processing_times) else processing_times[-1]
            
            metrics.append({
                'name': 'response_time_p50',
                'category': 'performance',
                'value': response_time_p50,
                'target_value': cls.TARGET_VALUES.get('response_time_p50'),
                'unit': 'seconds',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': total_requests,
                'metadata': {
                    'percentile': 50
                }
            })
            
            metrics.append({
                'name': 'response_time_p95',
                'category': 'performance',
                'value': response_time_p95,
                'target_value': cls.TARGET_VALUES.get('response_time_p95'),
                'unit': 'seconds',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': total_requests,
                'metadata': {
                    'percentile': 95
                }
            })
        
        # LLM Processing Time (p50)
        llm_requests = requests_with_metrics.filter(metrics__llm_processing_time__isnull=False)
        if llm_requests.exists():
            llm_times = list(llm_requests.values_list('metrics__llm_processing_time', flat=True))
            llm_times.sort()
            
            if llm_times:
                p50_index = int(len(llm_times) * 0.5)
                llm_processing_time_p50 = llm_times[p50_index] if p50_index < len(llm_times) else llm_times[-1]
                
                metrics.append({
                    'name': 'llm_processing_time_p50',
                    'category': 'performance',
                    'value': llm_processing_time_p50,
                    'target_value': cls.TARGET_VALUES.get('llm_processing_time_p50'),
                    'unit': 'seconds',
                    'period_start': period_start,
                    'period_end': period_end,
                    'sample_size': len(llm_times),
                    'metadata': {
                        'percentile': 50
                    }
                })
        
        # Throughput - пропускная способность
        time_delta = (period_end - period_start).total_seconds() / 60  # в минутах
        if time_delta > 0:
            completed_requests = requests_with_metrics.filter(status=ChatRequest.STATUS_COMPLETED).count()
            throughput = completed_requests / time_delta
            
            metrics.append({
                'name': 'throughput',
                'category': 'performance',
                'value': throughput,
                'target_value': cls.TARGET_VALUES.get('throughput'),
                'unit': 'requests_per_minute',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': completed_requests,
                'metadata': {
                    'time_delta_minutes': time_delta
                }
            })
        
        return metrics
    
    @classmethod
    def _calculate_reliability_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик надежности"""
        metrics = []
        
        all_requests = ChatRequest.objects.filter(requests_filter)
        total_requests = all_requests.count()
        
        if total_requests == 0:
            return metrics
        
        # Request Success Rate
        completed_requests = all_requests.filter(status=ChatRequest.STATUS_COMPLETED).count()
        request_success_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'request_success_rate',
            'category': 'reliability',
            'value': request_success_rate,
            'target_value': cls.TARGET_VALUES.get('request_success_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'completed_requests': completed_requests,
                'total_requests': total_requests
            }
        })
        
        # Error Rate
        failed_requests = all_requests.filter(status=ChatRequest.STATUS_FAILED).count()
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'error_rate',
            'category': 'reliability',
            'value': error_rate,
            'target_value': cls.TARGET_VALUES.get('error_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'failed_requests': failed_requests
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_security_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик безопасности"""
        metrics = []
        
        requests_with_metrics = ChatRequest.objects.filter(
            requests_filter,
            metrics__isnull=False
        ).select_related('metrics')
        
        total_requests = requests_with_metrics.count()
        if total_requests == 0:
            return metrics
        
        # AI Response Blocking Rate
        blocked_responses = requests_with_metrics.filter(metrics__response_blocked=True).count()
        ai_response_blocking_rate = (blocked_responses / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'ai_response_blocking_rate',
            'category': 'security',
            'value': ai_response_blocking_rate,
            'target_value': cls.TARGET_VALUES.get('ai_response_blocking_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'blocked_responses': blocked_responses
            }
        })
        
        # Message Blocking Rate (для оценки модерации входящих сообщений)
        blocked_messages = requests_with_metrics.filter(metrics__message_blocked=True).count()
        message_blocking_rate = (blocked_messages / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'message_blocking_rate',
            'category': 'security',
            'value': message_blocking_rate,
            'target_value': None,  # Нет целевого значения
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'blocked_messages': blocked_messages
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_user_experience_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик пользовательского опыта"""
        metrics = []
        
        requests_with_metrics = ChatRequest.objects.filter(
            requests_filter,
            metrics__isnull=False
        ).select_related('metrics')
        
        total_requests = requests_with_metrics.count()
        if total_requests == 0:
            return metrics
        
        # Task Completion Rate (запросы с успешными действиями)
        requests_with_actions = requests_with_metrics.filter(metrics__has_action=True)
        if requests_with_actions.exists():
            successful_tasks = requests_with_actions.filter(metrics__action_success=True).count()
            total_tasks = requests_with_actions.count()
            task_completion_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            metrics.append({
                'name': 'task_completion_rate',
                'category': 'user_experience',
                'value': task_completion_rate,
                'target_value': cls.TARGET_VALUES.get('task_completion_rate'),
                'unit': 'percent',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': total_tasks,
                'metadata': {
                    'successful_tasks': successful_tasks,
                    'total_tasks': total_tasks
                }
            })
        
        return metrics
    
    @classmethod
    def _calculate_file_processing_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик обработки файлов"""
        metrics = []
        
        requests_with_metrics = ChatRequest.objects.filter(
            requests_filter,
            metrics__isnull=False,
            metrics__has_files=True
        ).select_related('metrics')
        
        requests_with_files = requests_with_metrics.count()
        if requests_with_files == 0:
            return metrics
        
        # File Processing Success Rate
        total_files_processed = requests_with_metrics.aggregate(
            total=Sum('metrics__files_processed')
        )['total'] or 0
        
        total_files_failed = requests_with_metrics.aggregate(
            total=Sum('metrics__files_failed')
        )['total'] or 0
        
        total_files = total_files_processed + total_files_failed
        
        if total_files > 0:
            file_processing_success_rate = (total_files_processed / total_files * 100)
            
            metrics.append({
                'name': 'file_processing_success_rate',
                'category': 'file_processing',
                'value': file_processing_success_rate,
                'target_value': cls.TARGET_VALUES.get('file_processing_success_rate'),
                'unit': 'percent',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': total_files,
                'metadata': {
                    'total_files_processed': total_files_processed,
                    'total_files_failed': total_files_failed,
                    'total_files': total_files
                }
            })
        
        return metrics
    
    @classmethod
    def _calculate_data_accuracy_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик точности данных"""
        metrics = []
        
        requests_with_metrics = ChatRequest.objects.filter(
            requests_filter,
            metrics__isnull=False
        ).select_related('metrics')
        
        total_requests = requests_with_metrics.count()
        if total_requests == 0:
            return metrics
        
        # Context Utilization Rate
        requests_with_context = requests_with_metrics.filter(metrics__context_used=True).count()
        context_utilization_rate = (requests_with_context / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'context_utilization_rate',
            'category': 'data_accuracy',
            'value': context_utilization_rate,
            'target_value': cls.TARGET_VALUES.get('context_utilization_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'requests_with_context': requests_with_context
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_calendar_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик работы с календарем"""
        metrics = []
        
        # Получаем запросы с действиями календаря
        calendar_actions = ChatRequest.objects.filter(
            requests_filter,
            action__isnull=False
        ).exclude(action={})
        
        # Считаем CREATE_EVENT и UPDATE_EVENT
        create_events = calendar_actions.filter(
            action__action='CREATE_EVENT'
        ).count()
        
        update_events = calendar_actions.filter(
            action__action='UPDATE_EVENT'
        ).count()
        
        total_calendar_actions = create_events + update_events
        
        if total_calendar_actions > 0:
            # Event Creation Accuracy (упрощенно - считаем успешными, если нет ошибок)
            successful_creates = calendar_actions.filter(
                action__action='CREATE_EVENT',
                status=ChatRequest.STATUS_COMPLETED,
                error__isnull=True
            ).exclude(error='').count()
            
            if create_events > 0:
                event_creation_accuracy = (successful_creates / create_events * 100)
                
                metrics.append({
                    'name': 'event_creation_accuracy',
                    'category': 'calendar',
                    'value': event_creation_accuracy,
                    'target_value': cls.TARGET_VALUES.get('event_creation_accuracy'),
                    'unit': 'percent',
                    'period_start': period_start,
                    'period_end': period_end,
                    'sample_size': create_events,
                    'metadata': {
                        'successful_creates': successful_creates,
                        'total_creates': create_events
                    }
                })
            
            # Event Update Accuracy
            successful_updates = calendar_actions.filter(
                action__action='UPDATE_EVENT',
                status=ChatRequest.STATUS_COMPLETED,
                error__isnull=True
            ).exclude(error='').count()
            
            if update_events > 0:
                event_update_accuracy = (successful_updates / update_events * 100)
                
                metrics.append({
                    'name': 'event_update_accuracy',
                    'category': 'calendar',
                    'value': event_update_accuracy,
                    'target_value': cls.TARGET_VALUES.get('event_update_accuracy'),
                    'unit': 'percent',
                    'period_start': period_start,
                    'period_end': period_end,
                    'sample_size': update_events,
                    'metadata': {
                        'successful_updates': successful_updates,
                        'total_updates': update_events
                    }
                })
        
        return metrics
    
    @classmethod
    def _calculate_formatting_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик форматирования"""
        # Упрощенная реализация - можно расширить при необходимости
        metrics = []
        
        # Здесь можно добавить проверку таблиц и графиков в ответах
        # Для этого нужно анализировать содержимое response
        
        return metrics
    
    @classmethod
    def _calculate_user_engagement_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик активности пользователей"""
        metrics = []
        
        # Получаем все запросы за период
        all_requests = ChatRequest.objects.filter(requests_filter)
        total_requests = all_requests.count()
        
        if total_requests == 0:
            return metrics
        
        # 1. User Activity Rate - среднее количество запросов на пользователя
        # Используем User.objects из БД для точного подсчета
        
        # Получаем уникальных пользователей, которые имеют ChatRequest за период
        # Сначала получаем email из ChatHistory
        active_user_emails = ChatHistory.objects.filter(
            created_at__gte=period_start,
            created_at__lte=period_end
        ).values_list('user_email', flat=True).distinct()
        
        # Также получаем email из ChatRequest.user_data (для обратной совместимости)
        user_emails_from_requests = set()
        for request in all_requests.select_related().only('user_data'):
            user_data = request.user_data or {}
            email = user_data.get('email') or user_data.get('userEmail') or user_data.get('user_email')
            if email:
                user_emails_from_requests.add(email.lower())
        
        # Объединяем все email
        all_user_emails = set(active_user_emails) | user_emails_from_requests
        
        # Получаем уникальных пользователей из БД User по email
        unique_users_from_db = User.objects.filter(
            email__in=all_user_emails
        ).distinct()
        
        # Если есть пользователи в ChatHistory, но их нет в User, считаем по email
        if unique_users_from_db.count() == 0 and all_user_emails:
            # Fallback: используем количество уникальных email
            unique_users_count = len(all_user_emails)
            logger.warning(f"Пользователи найдены по email, но не в User.objects. Используется fallback: {unique_users_count}")
        else:
            unique_users_count = unique_users_from_db.count()
        
        # Если все еще нет пользователей, используем количество уникальных chat_id как fallback
        if unique_users_count == 0:
            unique_chats = ChatHistory.objects.filter(
                created_at__gte=period_start,
                created_at__lte=period_end
            ).values_list('chat_id', flat=True).distinct()
            unique_users_count = len(unique_chats) if unique_chats else 1
            logger.warning(f"Не найдено пользователей в БД. Используется fallback по chat_id: {unique_users_count}")
        
        # Рассчитываем среднюю активность
        if unique_users_count > 0:
            user_activity_rate = total_requests / unique_users_count
            
            metrics.append({
                'name': 'user_activity_rate',
                'category': 'user_engagement',
                'value': user_activity_rate,
                'target_value': cls.TARGET_VALUES.get('user_activity_rate'),
                'unit': 'requests_per_user',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': unique_users_count,
                'metadata': {
                    'total_requests': total_requests,
                    'unique_users': unique_users_count,
                    'users_from_db': unique_users_from_db.count() if unique_users_from_db.exists() else 0,
                    'users_from_email': len(all_user_emails)
                }
            })
        
        # 2. User Retention Rate - процент пользователей, вернувшихся через период
        # Используем User.objects из БД для расчета retention
        
        # Retention Rate за 7 дней
        if (period_end - period_start).days >= 7:
            # Базовый период (первые 7 дней)
            base_period_start = period_start
            base_period_end = period_start + timedelta(days=7)
            
            # Последующий период (следующие 7 дней после базового)
            retention_period_start = base_period_end
            retention_period_end = min(base_period_end + timedelta(days=7), period_end)
            
            if retention_period_end > retention_period_start:
                # Получаем пользователей из БД, которые были активны в базовом периоде
                base_user_emails = ChatHistory.objects.filter(
                    created_at__gte=base_period_start,
                    created_at__lt=base_period_end
                ).values_list('user_email', flat=True).distinct()
                
                # Получаем User объекты из БД
                base_users = User.objects.filter(email__in=base_user_emails).distinct()
                
                # Пользователи, вернувшиеся в последующем периоде
                returned_user_emails = ChatHistory.objects.filter(
                    created_at__gte=retention_period_start,
                    created_at__lte=retention_period_end,
                    user_email__in=base_user_emails
                ).values_list('user_email', flat=True).distinct()
                
                returned_users = User.objects.filter(email__in=returned_user_emails).distinct()
                
                # Fallback: если нет пользователей в БД, используем email
                if base_users.count() == 0 and base_user_emails:
                    base_users_count = len(base_user_emails)
                    returned_users_count = len(returned_user_emails)
                else:
                    base_users_count = base_users.count()
                    returned_users_count = returned_users.count()
                
                if base_users_count > 0:
                    retention_rate_7d = (returned_users_count / base_users_count) * 100
                    
                    metrics.append({
                        'name': 'user_retention_rate_7d',
                        'category': 'user_engagement',
                        'value': retention_rate_7d,
                        'target_value': cls.TARGET_VALUES.get('user_retention_rate_7d'),
                        'unit': 'percent',
                        'period_start': period_start,
                        'period_end': period_end,
                        'sample_size': base_users_count,
                        'metadata': {
                            'base_period_users': base_users_count,
                            'returned_users': returned_users_count,
                            'base_period_start': base_period_start.isoformat(),
                            'base_period_end': base_period_end.isoformat(),
                            'retention_period_start': retention_period_start.isoformat(),
                            'retention_period_end': retention_period_end.isoformat(),
                            'users_from_db': base_users.count() if base_users.exists() else 0
                        }
                    })
        
        # Retention Rate за 30 дней
        if (period_end - period_start).days >= 30:
            # Базовый период (первые 30 дней)
            base_period_start = period_start
            base_period_end = period_start + timedelta(days=30)
            
            # Последующий период (следующие 30 дней после базового)
            retention_period_start = base_period_end
            retention_period_end = min(base_period_end + timedelta(days=30), period_end)
            
            if retention_period_end > retention_period_start:
                # Получаем пользователей из БД, которые были активны в базовом периоде
                base_user_emails = ChatHistory.objects.filter(
                    created_at__gte=base_period_start,
                    created_at__lt=base_period_end
                ).values_list('user_email', flat=True).distinct()
                
                # Получаем User объекты из БД
                base_users = User.objects.filter(email__in=base_user_emails).distinct()
                
                # Пользователи, вернувшиеся в последующем периоде
                returned_user_emails = ChatHistory.objects.filter(
                    created_at__gte=retention_period_start,
                    created_at__lte=retention_period_end,
                    user_email__in=base_user_emails
                ).values_list('user_email', flat=True).distinct()
                
                returned_users = User.objects.filter(email__in=returned_user_emails).distinct()
                
                # Fallback: если нет пользователей в БД, используем email
                if base_users.count() == 0 and base_user_emails:
                    base_users_count = len(base_user_emails)
                    returned_users_count = len(returned_user_emails)
                else:
                    base_users_count = base_users.count()
                    returned_users_count = returned_users.count()
                
                if base_users_count > 0:
                    retention_rate_30d = (returned_users_count / base_users_count) * 100
                    
                    metrics.append({
                        'name': 'user_retention_rate_30d',
                        'category': 'user_engagement',
                        'value': retention_rate_30d,
                        'target_value': cls.TARGET_VALUES.get('user_retention_rate_30d'),
                        'unit': 'percent',
                        'period_start': period_start,
                        'period_end': period_end,
                        'sample_size': base_users_count,
                        'metadata': {
                            'base_period_users': base_users_count,
                            'returned_users': returned_users_count,
                            'base_period_start': base_period_start.isoformat(),
                            'base_period_end': base_period_end.isoformat(),
                            'retention_period_start': retention_period_start.isoformat(),
                            'retention_period_end': retention_period_end.isoformat(),
                            'users_from_db': base_users.count() if base_users.exists() else 0
                        }
                    })
        
        return metrics
    
    @classmethod
    def _calculate_request_length_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик длины запросов и ответов"""
        metrics = []
        
        all_requests = ChatRequest.objects.filter(requests_filter)
        total_requests = all_requests.count()
        
        if total_requests == 0:
            return metrics
        
        # Рассчитываем среднюю длину запросов
        request_lengths = [len(req.message or '') for req in all_requests]
        total_request_length = sum(request_lengths)
        avg_request_length = total_request_length / total_requests if total_requests > 0 else 0
        
        # Рассчитываем среднюю длину ответов
        response_lengths = [len(req.response or '') for req in all_requests if req.response]
        total_response_length = sum(response_lengths)
        completed_with_response = len(response_lengths)
        avg_response_length = total_response_length / completed_with_response if completed_with_response > 0 else 0
        
        # Соотношение длины ответа к запросу
        request_response_ratio = avg_response_length / avg_request_length if avg_request_length > 0 else 0
        
        # Процент длинных запросов (>200 символов)
        long_requests = sum(1 for length in request_lengths if length > 200)
        long_request_rate = (long_requests / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'avg_request_length',
            'category': 'request_analysis',
            'value': avg_request_length,
            'target_value': cls.TARGET_VALUES.get('avg_request_length'),
            'unit': 'characters',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'total_length': total_request_length,
                'total_requests': total_requests
            }
        })
        
        if completed_with_response > 0:
            metrics.append({
                'name': 'avg_response_length',
                'category': 'request_analysis',
                'value': avg_response_length,
                'target_value': cls.TARGET_VALUES.get('avg_response_length'),
                'unit': 'characters',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': completed_with_response,
                'metadata': {
                    'total_length': total_response_length,
                    'completed_with_response': completed_with_response
                }
            })
            
            metrics.append({
                'name': 'request_response_ratio',
                'category': 'request_analysis',
                'value': request_response_ratio,
                'target_value': cls.TARGET_VALUES.get('request_response_ratio'),
                'unit': 'ratio',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': completed_with_response,
                'metadata': {
                    'avg_request_length': avg_request_length,
                    'avg_response_length': avg_response_length
                }
            })
        
        metrics.append({
            'name': 'long_request_rate',
            'category': 'request_analysis',
            'value': long_request_rate,
            'target_value': cls.TARGET_VALUES.get('long_request_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'long_requests': long_requests,
                'total_requests': total_requests
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_chat_history_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик использования истории чата"""
        metrics = []
        
        all_requests = ChatRequest.objects.filter(requests_filter)
        total_requests = all_requests.count()
        
        if total_requests == 0:
            return metrics
        
        # Процент запросов с историей чата
        requests_with_history = sum(1 for req in all_requests if req.chat_history and len(req.chat_history) > 0)
        chat_history_usage_rate = (requests_with_history / total_requests * 100) if total_requests > 0 else 0
        
        # Средняя длина истории чата
        history_lengths = [len(req.chat_history or []) for req in all_requests if req.chat_history]
        avg_chat_history_length = sum(history_lengths) / len(history_lengths) if history_lengths else 0
        
        # Процент многошаговых диалогов (история > 2 сообщений)
        multi_turn = sum(1 for length in history_lengths if length > 2)
        multi_turn_conversation_rate = (multi_turn / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'chat_history_usage_rate',
            'category': 'user_experience',
            'value': chat_history_usage_rate,
            'target_value': cls.TARGET_VALUES.get('chat_history_usage_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'requests_with_history': requests_with_history,
                'total_requests': total_requests
            }
        })
        
        if history_lengths:
            metrics.append({
                'name': 'avg_chat_history_length',
                'category': 'user_experience',
                'value': avg_chat_history_length,
                'target_value': cls.TARGET_VALUES.get('avg_chat_history_length'),
                'unit': 'messages',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': len(history_lengths),
                'metadata': {
                    'total_history_lengths': sum(history_lengths)
                }
            })
        
        metrics.append({
            'name': 'multi_turn_conversation_rate',
            'category': 'user_experience',
            'value': multi_turn_conversation_rate,
            'target_value': cls.TARGET_VALUES.get('multi_turn_conversation_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'multi_turn_conversations': multi_turn,
                'total_requests': total_requests
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_usage_patterns_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик паттернов использования"""
        metrics = []
        
        all_requests = ChatRequest.objects.filter(requests_filter)
        total_requests = all_requests.count()
        
        if total_requests == 0:
            return metrics
        
        # Пиковые часы (9-18)
        peak_hours_requests = sum(1 for req in all_requests if 9 <= req.created_at.hour < 18)
        peak_hours_activity = (peak_hours_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Активность в выходные
        weekend_requests = sum(1 for req in all_requests if req.created_at.weekday() >= 5)
        weekend_activity_rate = (weekend_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Среднее количество запросов на сессию (группируем по chat_id из ChatHistory)
        # Используем ChatHistory для определения сессий
        chats = ChatHistory.objects.filter(
            created_at__gte=period_start,
            created_at__lte=period_end
        )
        total_chats = chats.count()
        total_messages = sum(chat.total_messages for chat in chats)
        avg_requests_per_session = total_messages / total_chats if total_chats > 0 else 0
        
        metrics.append({
            'name': 'peak_hours_activity',
            'category': 'usage_patterns',
            'value': peak_hours_activity,
            'target_value': cls.TARGET_VALUES.get('peak_hours_activity'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'peak_hours_requests': peak_hours_requests,
                'total_requests': total_requests
            }
        })
        
        metrics.append({
            'name': 'weekend_activity_rate',
            'category': 'usage_patterns',
            'value': weekend_activity_rate,
            'target_value': cls.TARGET_VALUES.get('weekend_activity_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'weekend_requests': weekend_requests,
                'total_requests': total_requests
            }
        })
        
        if total_chats > 0:
            metrics.append({
                'name': 'avg_requests_per_session',
                'category': 'usage_patterns',
                'value': avg_requests_per_session,
                'target_value': cls.TARGET_VALUES.get('avg_requests_per_session'),
                'unit': 'requests',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': total_chats,
                'metadata': {
                    'total_messages': total_messages,
                    'total_chats': total_chats
                }
            })
        
        return metrics
    
    @classmethod
    def _calculate_error_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик ошибок и повторных запросов"""
        metrics = []
        
        all_requests = ChatRequest.objects.filter(requests_filter)
        total_requests = all_requests.count()
        
        if total_requests == 0:
            return metrics
        
        # Процент запросов с ошибками
        failed_requests = all_requests.filter(status=ChatRequest.STATUS_FAILED)
        failed_count = failed_requests.count()
        
        # Анализ типов ошибок
        timeout_errors = sum(1 for req in failed_requests if 'timeout' in (req.error or '').lower())
        connection_errors = sum(1 for req in failed_requests if 'connection' in (req.error or '').lower() or 'connect' in (req.error or '').lower())
        
        timeout_rate = (timeout_errors / total_requests * 100) if total_requests > 0 else 0
        connection_error_rate = (connection_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Процент успешных запросов после ошибки (анализ по пользователям)
        # Получаем пользователей с ошибками
        users_with_errors = set()
        for req in failed_requests:
            user_data = req.user_data or {}
            email = user_data.get('email') or user_data.get('userEmail') or user_data.get('user_email')
            if email:
                users_with_errors.add(email)
        
        # Проверяем, сколько из них сделали успешные запросы после ошибки
        recovery_count = 0
        if users_with_errors:
            for email in users_with_errors:
                # Находим первую ошибку пользователя
                first_error = failed_requests.filter(
                    user_data__email=email
                ).order_by('created_at').first()
                
                if first_error:
                    # Проверяем, есть ли успешные запросы после ошибки
                    successful_after = all_requests.filter(
                        created_at__gt=first_error.created_at,
                        status=ChatRequest.STATUS_COMPLETED
                    ).filter(
                        Q(user_data__email=email) | Q(user_data__userEmail=email)
                    ).exists()
                    
                    if successful_after:
                        recovery_count += 1
            
            error_recovery_rate = (recovery_count / len(users_with_errors) * 100) if users_with_errors else 0
        else:
            error_recovery_rate = 0
        
        # Процент повторных запросов (упрощенная версия - запросы с одинаковым текстом)
        request_texts = {}
        for req in all_requests:
            text = (req.message or '').strip().lower()[:100]  # Первые 100 символов
            if text:
                request_texts[text] = request_texts.get(text, 0) + 1
        
        retry_requests = sum(1 for count in request_texts.values() if count > 1)
        retry_rate = (retry_requests / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'retry_rate',
            'category': 'reliability',
            'value': retry_rate,
            'target_value': cls.TARGET_VALUES.get('retry_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'retry_requests': retry_requests,
                'total_requests': total_requests
            }
        })
        
        if users_with_errors:
            metrics.append({
                'name': 'error_recovery_rate',
                'category': 'reliability',
                'value': error_recovery_rate,
                'target_value': cls.TARGET_VALUES.get('error_recovery_rate'),
                'unit': 'percent',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': len(users_with_errors),
                'metadata': {
                    'users_with_errors': len(users_with_errors),
                    'recovered_users': recovery_count if users_with_errors else 0
                }
            })
        
        metrics.append({
            'name': 'timeout_rate',
            'category': 'reliability',
            'value': timeout_rate,
            'target_value': cls.TARGET_VALUES.get('timeout_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'timeout_errors': timeout_errors,
                'total_requests': total_requests
            }
        })
        
        metrics.append({
            'name': 'connection_error_rate',
            'category': 'reliability',
            'value': connection_error_rate,
            'target_value': cls.TARGET_VALUES.get('connection_error_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'connection_errors': connection_errors,
                'total_requests': total_requests
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_action_conversion_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик конверсии действий"""
        metrics = []
        
        requests_with_metrics = ChatRequest.objects.filter(
            requests_filter,
            metrics__isnull=False
        ).select_related('metrics')
        
        total_requests = requests_with_metrics.count()
        
        if total_requests == 0:
            return metrics
        
        # Запросы с действиями
        requests_with_actions = requests_with_metrics.filter(metrics__has_action=True)
        action_count = requests_with_actions.count()
        
        # Процент запросов, приводящих к действию
        action_conversion_rate = (action_count / total_requests * 100) if total_requests > 0 else 0
        
        # Процент запросов с попыткой действия (включая неудачные)
        action_attempts = requests_with_metrics.filter(
            Q(metrics__has_action=True) | Q(action__isnull=False)
        ).exclude(action={}).count()
        action_attempt_rate = (action_attempts / total_requests * 100) if total_requests > 0 else 0
        
        # Процент неудачных действий
        failed_actions = requests_with_actions.filter(metrics__action_success=False).count()
        action_failure_rate = (failed_actions / action_count * 100) if action_count > 0 else 0
        
        # Среднее количество действий на запрос
        total_actions = sum(
            len(req.action or {}) if isinstance(req.action, dict) else (1 if req.action else 0)
            for req in requests_with_actions
        )
        avg_actions_per_request = total_actions / action_count if action_count > 0 else 0
        
        metrics.append({
            'name': 'action_conversion_rate',
            'category': 'action_performance',
            'value': action_conversion_rate,
            'target_value': cls.TARGET_VALUES.get('action_conversion_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'requests_with_actions': action_count,
                'total_requests': total_requests
            }
        })
        
        metrics.append({
            'name': 'action_attempt_rate',
            'category': 'action_performance',
            'value': action_attempt_rate,
            'target_value': cls.TARGET_VALUES.get('action_attempt_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'action_attempts': action_attempts,
                'total_requests': total_requests
            }
        })
        
        if action_count > 0:
            metrics.append({
                'name': 'action_failure_rate',
                'category': 'action_performance',
                'value': action_failure_rate,
                'target_value': cls.TARGET_VALUES.get('action_failure_rate'),
                'unit': 'percent',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': action_count,
                'metadata': {
                    'failed_actions': failed_actions,
                    'total_actions': action_count
                }
            })
            
            metrics.append({
                'name': 'avg_actions_per_request',
                'category': 'action_performance',
                'value': avg_actions_per_request,
                'target_value': cls.TARGET_VALUES.get('avg_actions_per_request'),
                'unit': 'actions',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': action_count,
                'metadata': {
                    'total_actions': total_actions,
                    'requests_with_actions': action_count
                }
            })
        
        return metrics
    
    @classmethod
    def _calculate_feature_usage_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик использования функций"""
        metrics = []
        
        all_requests = ChatRequest.objects.filter(requests_filter)
        total_requests = all_requests.count()
        
        if total_requests == 0:
            return metrics
        
        # Процент запросов с файлами
        requests_with_files = sum(1 for req in all_requests if req.files_data and len(req.files_data) > 0)
        file_attachment_rate = (requests_with_files / total_requests * 100) if total_requests > 0 else 0
        
        # Процент запросов с действиями календаря
        calendar_actions = sum(1 for req in all_requests 
                              if req.action and isinstance(req.action, dict) 
                              and ('CREATE_EVENT' in str(req.action) or 'UPDATE_EVENT' in str(req.action) or 'DELETE_EVENT' in str(req.action)))
        calendar_action_rate = (calendar_actions / total_requests * 100) if total_requests > 0 else 0
        
        # Процент запросов с несколькими функциями
        multi_feature = sum(1 for req in all_requests 
                           if (req.files_data and len(req.files_data) > 0) and 
                           (req.action and isinstance(req.action, dict) and len(req.action) > 0))
        multi_feature_usage_rate = (multi_feature / total_requests * 100) if total_requests > 0 else 0
        
        # Процент комбинаций функций (файл + календарь)
        feature_combination = sum(1 for req in all_requests 
                                  if (req.files_data and len(req.files_data) > 0) and
                                  (req.action and isinstance(req.action, dict) and 
                                   ('CREATE_EVENT' in str(req.action) or 'UPDATE_EVENT' in str(req.action))))
        feature_combination_rate = (feature_combination / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'file_attachment_rate',
            'category': 'feature_usage',
            'value': file_attachment_rate,
            'target_value': cls.TARGET_VALUES.get('file_attachment_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'requests_with_files': requests_with_files,
                'total_requests': total_requests
            }
        })
        
        metrics.append({
            'name': 'calendar_action_rate',
            'category': 'feature_usage',
            'value': calendar_action_rate,
            'target_value': cls.TARGET_VALUES.get('calendar_action_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'calendar_actions': calendar_actions,
                'total_requests': total_requests
            }
        })
        
        metrics.append({
            'name': 'multi_feature_usage_rate',
            'category': 'feature_usage',
            'value': multi_feature_usage_rate,
            'target_value': cls.TARGET_VALUES.get('multi_feature_usage_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'multi_feature_requests': multi_feature,
                'total_requests': total_requests
            }
        })
        
        metrics.append({
            'name': 'feature_combination_rate',
            'category': 'feature_usage',
            'value': feature_combination_rate,
            'target_value': cls.TARGET_VALUES.get('feature_combination_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'feature_combination_requests': feature_combination,
                'total_requests': total_requests
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_context_quality_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик качества контекста"""
        metrics = []
        
        all_requests = ChatRequest.objects.filter(requests_filter)
        total_requests = all_requests.count()
        
        if total_requests == 0:
            return metrics
        
        # Процент запросов с полным контекстом (есть email и другие данные)
        requests_with_context = 0
        requests_with_complete_context = 0
        requests_without_context = 0
        
        for req in all_requests:
            user_data = req.user_data or {}
            if user_data:
                requests_with_context += 1
                # Проверяем полноту контекста (есть email и хотя бы еще одно поле)
                email = user_data.get('email') or user_data.get('userEmail') or user_data.get('user_email')
                if email and len(user_data) > 1:
                    requests_with_complete_context += 1
            else:
                requests_without_context += 1
        
        context_completeness_rate = (requests_with_complete_context / total_requests * 100) if total_requests > 0 else 0
        missing_context_rate = (requests_without_context / total_requests * 100) if total_requests > 0 else 0
        
        # Эффективность использования контекста (запросы с контекстом, которые привели к успешным действиям)
        requests_with_metrics = ChatRequest.objects.filter(
            requests_filter,
            metrics__isnull=False,
            metrics__context_used=True
        ).select_related('metrics')
        
        context_used_count = requests_with_metrics.count()
        context_successful = requests_with_metrics.filter(
            Q(metrics__action_success=True) | Q(status=ChatRequest.STATUS_COMPLETED)
        ).count()
        
        context_utilization_effectiveness = (context_successful / context_used_count * 100) if context_used_count > 0 else 0
        
        metrics.append({
            'name': 'context_completeness_rate',
            'category': 'data_accuracy',
            'value': context_completeness_rate,
            'target_value': cls.TARGET_VALUES.get('context_completeness_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'requests_with_complete_context': requests_with_complete_context,
                'total_requests': total_requests
            }
        })
        
        metrics.append({
            'name': 'context_utilization_effectiveness',
            'category': 'data_accuracy',
            'value': context_utilization_effectiveness,
            'target_value': cls.TARGET_VALUES.get('context_utilization_effectiveness'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': context_used_count,
            'metadata': {
                'context_successful': context_successful,
                'context_used_count': context_used_count
            }
        })
        
        metrics.append({
            'name': 'missing_context_rate',
            'category': 'data_accuracy',
            'value': missing_context_rate,
            'target_value': cls.TARGET_VALUES.get('missing_context_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'requests_without_context': requests_without_context,
                'total_requests': total_requests
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_session_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик сессий пользователей"""
        metrics = []
        
        # Используем ChatHistory для анализа сессий
        chats = ChatHistory.objects.filter(
            created_at__gte=period_start,
            created_at__lte=period_end
        )
        
        total_chats = chats.count()
        
        if total_chats == 0:
            return metrics
        
        # Средняя длительность сессии (разница между первым и последним сообщением)
        session_durations = []
        for chat in chats:
            if chat.last_message_at and chat.created_at:
                duration = (chat.last_message_at - chat.created_at).total_seconds() / 60  # в минутах
                if duration > 0:
                    session_durations.append(duration)
        
        avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0
        
        # Среднее время между запросами (анализ по ChatRequest)
        all_requests = ChatRequest.objects.filter(requests_filter).order_by('created_at')
        
        # Группируем запросы по пользователям и считаем среднее время между запросами
        user_request_times = {}
        for req in all_requests:
            user_data = req.user_data or {}
            email = user_data.get('email') or user_data.get('userEmail') or user_data.get('user_email')
            if email:
                if email not in user_request_times:
                    user_request_times[email] = []
                user_request_times[email].append(req.created_at)
        
        time_differences = []
        for email, times in user_request_times.items():
            if len(times) > 1:
                for i in range(len(times) - 1):
                    diff = (times[i+1] - times[i]).total_seconds()
                    if diff > 0:
                        time_differences.append(diff)
        
        avg_time_between_requests = sum(time_differences) / len(time_differences) if time_differences else 0
        
        # Процент завершенных сессий (сессии с >3 сообщениями считаются завершенными)
        completed_sessions = sum(1 for chat in chats if chat.total_messages >= 3)
        session_completion_rate = (completed_sessions / total_chats * 100) if total_chats > 0 else 0
        
        # Процент возвращающихся пользователей (уже есть в user_engagement, но можно добавить здесь)
        unique_users = set(chats.values_list('user_email', flat=True).distinct())
        returning_users = set()
        
        # Проверяем, есть ли у пользователей чаты до этого периода
        for email in unique_users:
            previous_chats = ChatHistory.objects.filter(
                user_email=email,
                created_at__lt=period_start
            ).exists()
            if previous_chats:
                returning_users.add(email)
        
        returning_user_rate = (len(returning_users) / len(unique_users) * 100) if unique_users else 0
        
        if session_durations:
            metrics.append({
                'name': 'avg_session_duration',
                'category': 'user_engagement',
                'value': avg_session_duration,
                'target_value': cls.TARGET_VALUES.get('avg_session_duration'),
                'unit': 'minutes',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': len(session_durations),
                'metadata': {
                    'total_duration': sum(session_durations),
                    'total_sessions': len(session_durations)
                }
            })
        
        if time_differences:
            metrics.append({
                'name': 'avg_time_between_requests',
                'category': 'user_engagement',
                'value': avg_time_between_requests,
                'target_value': cls.TARGET_VALUES.get('avg_time_between_requests'),
                'unit': 'seconds',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': len(time_differences),
                'metadata': {
                    'total_differences': len(time_differences)
                }
            })
        
        metrics.append({
            'name': 'session_completion_rate',
            'category': 'user_engagement',
            'value': session_completion_rate,
            'target_value': cls.TARGET_VALUES.get('session_completion_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_chats,
            'metadata': {
                'completed_sessions': completed_sessions,
                'total_chats': total_chats
            }
        })
        
        if unique_users:
            metrics.append({
                'name': 'returning_user_rate',
                'category': 'user_engagement',
                'value': returning_user_rate,
                'target_value': cls.TARGET_VALUES.get('returning_user_rate'),
                'unit': 'percent',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': len(unique_users),
                'metadata': {
                    'returning_users': len(returning_users),
                    'unique_users': len(unique_users)
                }
            })
        
        return metrics
    
    @classmethod
    def _calculate_content_analysis_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик анализа контента"""
        metrics = []
        
        all_requests = ChatRequest.objects.filter(requests_filter)
        total_requests = all_requests.count()
        
        if total_requests == 0:
            return metrics
        
        # Анализ уникальности запросов
        request_texts = {}
        for req in all_requests:
            text = (req.message or '').strip().lower()[:200]  # Первые 200 символов для сравнения
            if text:
                request_texts[text] = request_texts.get(text, 0) + 1
        
        unique_texts = sum(1 for count in request_texts.values() if count == 1)
        unique_request_rate = (unique_texts / total_requests * 100) if total_requests > 0 else 0
        
        repeated_texts = sum(1 for count in request_texts.values() if count > 1)
        repeated_request_rate = (repeated_texts / total_requests * 100) if total_requests > 0 else 0
        
        metrics.append({
            'name': 'unique_request_rate',
            'category': 'content_analysis',
            'value': unique_request_rate,
            'target_value': cls.TARGET_VALUES.get('unique_request_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'unique_texts': unique_texts,
                'total_requests': total_requests
            }
        })
        
        metrics.append({
            'name': 'repeated_request_rate',
            'category': 'content_analysis',
            'value': repeated_request_rate,
            'target_value': cls.TARGET_VALUES.get('repeated_request_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'repeated_texts': repeated_texts,
                'total_requests': total_requests
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_multimodal_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик мультимодальности"""
        metrics = []
        
        all_requests = ChatRequest.objects.filter(requests_filter)
        total_requests = all_requests.count()
        
        if total_requests == 0:
            return metrics
        
        # Процент запросов с изображениями
        requests_with_images = 0
        successful_image_processing = 0
        
        for req in all_requests:
            files = req.files_data or []
            has_images = any(
                f.get('type', '').startswith('image/') or 
                f.get('name', '').lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))
                for f in files
            )
            
            if has_images:
                requests_with_images += 1
                # Проверяем успешность обработки (если есть ответ и нет ошибки)
                if req.status == ChatRequest.STATUS_COMPLETED and not req.error:
                    successful_image_processing += 1
        
        image_processing_rate = (requests_with_images / total_requests * 100) if total_requests > 0 else 0
        image_processing_success_rate = (successful_image_processing / requests_with_images * 100) if requests_with_images > 0 else 0
        
        # Процент мультимодальных запросов (текст + файлы)
        multimodal_requests = sum(1 for req in all_requests 
                                if req.message and req.files_data and len(req.files_data) > 0)
        multimodal_request_rate = (multimodal_requests / total_requests * 100) if total_requests > 0 else 0
        
        if requests_with_images > 0:
            metrics.append({
                'name': 'image_processing_rate',
                'category': 'multimodal',
                'value': image_processing_rate,
                'target_value': cls.TARGET_VALUES.get('image_processing_rate'),
                'unit': 'percent',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': total_requests,
                'metadata': {
                    'requests_with_images': requests_with_images,
                    'total_requests': total_requests
                }
            })
            
            metrics.append({
                'name': 'image_processing_success_rate',
                'category': 'multimodal',
                'value': image_processing_success_rate,
                'target_value': cls.TARGET_VALUES.get('image_processing_success_rate'),
                'unit': 'percent',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': requests_with_images,
                'metadata': {
                    'successful_image_processing': successful_image_processing,
                    'requests_with_images': requests_with_images
                }
            })
        
        metrics.append({
            'name': 'multimodal_request_rate',
            'category': 'multimodal',
            'value': multimodal_request_rate,
            'target_value': cls.TARGET_VALUES.get('multimodal_request_rate'),
            'unit': 'percent',
            'period_start': period_start,
            'period_end': period_end,
            'sample_size': total_requests,
            'metadata': {
                'multimodal_requests': multimodal_requests,
                'total_requests': total_requests
            }
        })
        
        return metrics
    
    @classmethod
    def _calculate_performance_by_type_metrics(cls, requests_filter, period_start, period_end):
        """Расчет метрик производительности по типам запросов"""
        metrics = []
        
        requests_with_metrics = ChatRequest.objects.filter(
            requests_filter,
            metrics__isnull=False
        ).select_related('metrics')
        
        total_requests = requests_with_metrics.count()
        
        if total_requests == 0:
            return metrics
        
        # Запросы с действиями
        action_requests = requests_with_metrics.filter(metrics__has_action=True)
        action_times = [req.metrics.processing_time for req in action_requests if req.metrics.processing_time]
        if action_times:
            avg_action_time = sum(action_times) / len(action_times)
        else:
            avg_action_time = 0
        
        # Запросы с файлами
        file_requests = requests_with_metrics.filter(metrics__has_files=True)
        file_times = [req.metrics.processing_time for req in file_requests if req.metrics.processing_time]
        if file_times:
            avg_file_time = sum(file_times) / len(file_times)
        else:
            avg_file_time = 0
        
        # Простые запросы (без действий и файлов)
        simple_requests = requests_with_metrics.filter(
            metrics__has_action=False,
            metrics__has_files=False
        )
        simple_times = [req.metrics.processing_time for req in simple_requests if req.metrics.processing_time]
        if simple_times:
            avg_simple_time = sum(simple_times) / len(simple_times)
        else:
            avg_simple_time = 0
        
        if action_times:
            metrics.append({
                'name': 'action_request_processing_time',
                'category': 'performance',
                'value': avg_action_time,
                'target_value': cls.TARGET_VALUES.get('action_request_processing_time'),
                'unit': 'seconds',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': len(action_times),
                'metadata': {
                    'action_requests': len(action_times)
                }
            })
        
        if file_times:
            metrics.append({
                'name': 'file_request_processing_time',
                'category': 'performance',
                'value': avg_file_time,
                'target_value': cls.TARGET_VALUES.get('file_request_processing_time'),
                'unit': 'seconds',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': len(file_times),
                'metadata': {
                    'file_requests': len(file_times)
                }
            })
        
        if simple_times:
            metrics.append({
                'name': 'simple_request_processing_time',
                'category': 'performance',
                'value': avg_simple_time,
                'target_value': cls.TARGET_VALUES.get('simple_request_processing_time'),
                'unit': 'seconds',
                'period_start': period_start,
                'period_end': period_end,
                'sample_size': len(simple_times),
                'metadata': {
                    'simple_requests': len(simple_times)
                }
            })
        
        return metrics
    
    @classmethod
    def create_request_metrics(cls, chat_request, processing_time=None, llm_time=None, 
                                has_action=False, action_success=None, files_data=None,
                                message_blocked=False, response_blocked=False,
                                context_used=False, response_text=None):
        """
        Создает метрики для конкретного запроса
        
        Args:
            chat_request: Экземпляр ChatRequest
            processing_time: Время обработки в секундах
            llm_time: Время обработки LLM в секундах
            has_action: Есть ли действие в ответе
            action_success: Успешно ли выполнено действие
            files_data: Данные о файлах
            message_blocked: Заблокировано ли сообщение
            response_blocked: Заблокирован ли ответ
            context_used: Использован ли контекст
            response_text: Текст ответа
        """
        metrics, created = ChatRequestMetrics.objects.get_or_create(
            chat_request=chat_request,
            defaults={
                'processing_time': processing_time,
                'llm_processing_time': llm_time,
                'has_action': has_action,
                'action_success': action_success,
                'has_files': bool(files_data and len(files_data) > 0),
                'files_processed': 0,
                'files_failed': 0,
                'message_blocked': message_blocked,
                'response_blocked': response_blocked,
                'context_used': context_used,
                'response_length': len(response_text) if response_text else 0,
            }
        )
        
        if not created:
            # Обновляем существующие метрики
            if processing_time is not None:
                metrics.processing_time = processing_time
            if llm_time is not None:
                metrics.llm_processing_time = llm_time
            metrics.has_action = has_action
            if action_success is not None:
                metrics.action_success = action_success
            metrics.has_files = bool(files_data and len(files_data) > 0)
            metrics.message_blocked = message_blocked
            metrics.response_blocked = response_blocked
            metrics.context_used = context_used
            if response_text:
                metrics.response_length = len(response_text)
            metrics.save()
        
        # Подсчитываем файлы
        if files_data:
            metrics.files_processed = len([f for f in files_data if f.get('processed', False)])
            metrics.files_failed = len(files_data) - metrics.files_processed
            metrics.save()
        
        return metrics

