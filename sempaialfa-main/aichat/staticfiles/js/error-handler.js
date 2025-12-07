/**
 * Универсальная система обработки ошибок
 * Предоставляет централизованную обработку ошибок с логированием и уведомлениями
 */

(function() {
    'use strict';

    // Классификация типов ошибок
    const ErrorTypes = {
        NETWORK: 'network',
        API: 'api',
        VALIDATION: 'validation',
        PERMISSION: 'permission',
        NOT_FOUND: 'not_found',
        SERVER: 'server',
        TIMEOUT: 'timeout',
        UNKNOWN: 'unknown'
    };

    // Уровни серьезности ошибок
    const ErrorSeverity = {
        LOW: 'low',
        MEDIUM: 'medium',
        HIGH: 'high',
        CRITICAL: 'critical'
    };

    /**
     * Определяет тип ошибки на основе объекта ошибки
     */
    function classifyError(error) {
        if (!error) return { type: ErrorTypes.UNKNOWN, severity: ErrorSeverity.MEDIUM };

        // Сетевые ошибки
        if (error instanceof TypeError && error.message.includes('fetch')) {
            return { type: ErrorTypes.NETWORK, severity: ErrorSeverity.HIGH };
        }
        if (error.name === 'NetworkError' || error.name === 'TypeError') {
            return { type: ErrorTypes.NETWORK, severity: ErrorSeverity.HIGH };
        }

        // Ошибки таймаута
        if (error.name === 'TimeoutError' || error.message?.includes('timeout')) {
            return { type: ErrorTypes.TIMEOUT, severity: ErrorSeverity.MEDIUM };
        }

        // API ошибки
        if (error.status || error.statusCode) {
            const status = error.status || error.statusCode;
            if (status >= 500) {
                return { type: ErrorTypes.SERVER, severity: ErrorSeverity.HIGH };
            } else if (status === 404) {
                return { type: ErrorTypes.NOT_FOUND, severity: ErrorSeverity.MEDIUM };
            } else if (status === 403 || status === 401) {
                return { type: ErrorTypes.PERMISSION, severity: ErrorSeverity.HIGH };
            } else {
                return { type: ErrorTypes.API, severity: ErrorSeverity.MEDIUM };
            }
        }

        // Ошибки валидации
        if (error.validation || error.errors) {
            return { type: ErrorTypes.VALIDATION, severity: ErrorSeverity.LOW };
        }

        return { type: ErrorTypes.UNKNOWN, severity: ErrorSeverity.MEDIUM };
    }

    /**
     * Форматирует сообщение об ошибке для пользователя
     */
    function formatErrorMessage(error, errorInfo) {
        const userMessages = {
            [ErrorTypes.NETWORK]: 'Проблемы с подключением к интернету. Проверьте соединение и попробуйте снова.',
            [ErrorTypes.TIMEOUT]: 'Превышено время ожидания ответа. Попробуйте повторить запрос.',
            [ErrorTypes.SERVER]: 'Ошибка на сервере. Мы уже работаем над исправлением проблемы.',
            [ErrorTypes.NOT_FOUND]: 'Запрашиваемый ресурс не найден.',
            [ErrorTypes.PERMISSION]: 'У вас нет доступа к этому ресурсу. Проверьте права доступа.',
            [ErrorTypes.API]: 'Ошибка при выполнении запроса. Попробуйте позже.',
            [ErrorTypes.VALIDATION]: error.message || 'Проверьте правильность введенных данных.',
            [ErrorTypes.UNKNOWN]: 'Произошла непредвиденная ошибка. Попробуйте обновить страницу.'
        };

        // Если есть пользовательское сообщение, используем его
        if (error.userMessage) {
            return error.userMessage;
        }

        // Если есть понятное сообщение об ошибке
        if (error.message && !error.message.includes('fetch') && !error.message.includes('Network')) {
            return error.message;
        }

        return userMessages[errorInfo.type] || userMessages[ErrorTypes.UNKNOWN];
    }

    /**
     * Логирует ошибку
     */
    function logError(error, errorInfo, context = {}) {
        const errorLog = {
            timestamp: new Date().toISOString(),
            type: errorInfo.type,
            severity: errorInfo.severity,
            message: error.message || String(error),
            stack: error.stack,
            context: context,
            url: window.location.href,
            userAgent: navigator.userAgent
        };

        // Логируем в консоль для разработки
        // Убрали проверку process.env, так как process не доступен в браузере
        if (window.DEBUG_MODE !== false) {
            console.error('Ошибка:', errorLog);
        }

        // Сохраняем в localStorage для последующего анализа
        try {
            const errorLogs = JSON.parse(localStorage.getItem('errorLogs') || '[]');
            errorLogs.push(errorLog);
            // Храним только последние 50 ошибок
            if (errorLogs.length > 50) {
                errorLogs.shift();
            }
            localStorage.setItem('errorLogs', JSON.stringify(errorLogs));
        } catch (e) {
            console.warn('Не удалось сохранить лог ошибки:', e);
        }

        // Отправляем критичные ошибки на сервер (если есть endpoint)
        if (errorInfo.severity === ErrorSeverity.CRITICAL || errorInfo.severity === ErrorSeverity.HIGH) {
            sendErrorToServer(errorLog).catch(() => {
                // Игнорируем ошибки при отправке логов
            });
        }
    }

    /**
     * Отправляет ошибку на сервер для анализа
     */
    async function sendErrorToServer(errorLog) {
        try {
            // Используем fetchWithErrorHandling, но с silent режимом, чтобы не создавать бесконечный цикл
            await fetch('/api/error-log/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(errorLog)
            }).catch(() => {
                // Игнорируем ошибки при отправке логов, чтобы не создавать бесконечный цикл
            });
        } catch (e) {
            // Игнорируем ошибки при отправке
        }
    }

    /**
     * Показывает уведомление об ошибке пользователю
     */
    function showErrorNotification(message, errorInfo, options = {}) {
        const {
            duration = errorInfo.severity === ErrorSeverity.CRITICAL ? 0 : 5000,
            showModal = errorInfo.severity === ErrorSeverity.CRITICAL || errorInfo.severity === ErrorSeverity.HIGH,
            silent = false
        } = options;

        if (silent) return;

        // Показываем модальное окно для критичных ошибок
        if (showModal && typeof showErrorModal === 'function') {
            showErrorModal(message);
            return;
        }

        // Показываем toast уведомление
        if (typeof showToast === 'function') {
            showToast(message, 'error', duration);
        } else {
            // Используем встроенную функцию showToast
            showToastNotification(message, 'error', duration);
        }
    }

    /**
     * Основная функция обработки ошибок
     */
    window.handleError = function(error, context = {}, options = {}) {
        const errorInfo = classifyError(error);
        const userMessage = formatErrorMessage(error, errorInfo);
        
        // Логируем ошибку
        logError(error, errorInfo, context);

        // Показываем уведомление пользователю
        showErrorNotification(userMessage, errorInfo, options);

        // Возвращаем информацию об ошибке для дальнейшей обработки
        return {
            error: error,
            errorInfo: errorInfo,
            userMessage: userMessage,
            handled: true
        };
    };

    /**
     * Обработка ошибок из промисов
     */
    window.handlePromiseError = function(promise, context = {}, options = {}) {
        return promise.catch(error => {
            handleError(error, context, options);
            throw error; // Пробрасываем ошибку дальше
        });
    };

    /**
     * Обертка для асинхронных функций с обработкой ошибок
     */
    window.withErrorHandling = async function(asyncFunction, context = {}, options = {}) {
        try {
            return await asyncFunction();
        } catch (error) {
            return handleError(error, context, options);
        }
    };

    /**
     * Retry механизм для повторных попыток при ошибках
     */
    window.retryOnError = async function(asyncFunction, options = {}) {
        const {
            maxRetries = 3,
            delay = 1000,
            retryableErrors = [ErrorTypes.NETWORK, ErrorTypes.TIMEOUT, ErrorTypes.SERVER],
            onRetry = null
        } = options;

        let lastError;
        
        for (let attempt = 0; attempt <= maxRetries; attempt++) {
            try {
                return await asyncFunction();
            } catch (error) {
                lastError = error;
                const errorInfo = classifyError(error);
                
                // Проверяем, можно ли повторить попытку
                if (attempt < maxRetries && retryableErrors.includes(errorInfo.type)) {
                    if (onRetry) {
                        onRetry(attempt + 1, maxRetries, error);
                    }
                    
                    // Экспоненциальная задержка
                    const waitTime = delay * Math.pow(2, attempt);
                    await new Promise(resolve => setTimeout(resolve, waitTime));
                    continue;
                }
                
                // Если нельзя повторить или закончились попытки
                throw error;
            }
        }
        
        throw lastError;
    };

    /**
     * Обработка сетевых запросов с улучшенной обработкой ошибок
     */
    window.fetchWithErrorHandling = async function(url, options = {}, context = {}) {
        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch {
                    errorData = { message: `HTTP ${response.status}: ${response.statusText}` };
                }
                
                const error = new Error(errorData.message || `HTTP ${response.status}`);
                error.status = response.status;
                error.data = errorData;
                
                throw error;
            }
            
            return response;
        } catch (error) {
            // Улучшаем сообщение об ошибке
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                error.userMessage = 'Не удалось подключиться к серверу. Проверьте подключение к интернету.';
            }
            
            handleError(error, { ...context, url, method: options.method || 'GET' });
            throw error;
        }
    };

    /**
     * Глобальная обработка необработанных ошибок
     */
    window.addEventListener('error', function(event) {
        handleError(event.error || new Error(event.message), {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno
        }, { silent: false });
    });

    /**
     * Обработка необработанных отклоненных промисов
     */
    window.addEventListener('unhandledrejection', function(event) {
        handleError(event.reason, {
            promise: true
        }, { silent: false });
        
        // Предотвращаем вывод в консоль браузера
        event.preventDefault();
    });

    /**
     * Функция для получения логов ошибок (для отладки)
     */
    window.getErrorLogs = function() {
        try {
            return JSON.parse(localStorage.getItem('errorLogs') || '[]');
        } catch {
            return [];
        }
    };

    /**
     * Функция для очистки логов ошибок
     */
    window.clearErrorLogs = function() {
        localStorage.removeItem('errorLogs');
    };

    /**
     * Функция для показа toast уведомлений
     */
    function showToastNotification(message, type = 'info', duration = 5000) {
        // Создаем контейнер для toast, если его нет
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        // Создаем toast элемент
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            error: '❌',
            warning: '⚠️',
            success: '✅',
            info: 'ℹ️'
        };
        
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        container.appendChild(toast);
        
        // Автоматически удаляем через указанное время
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.add('toast-exit');
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }, duration);
        }
        
        return toast;
    }

    // Экспортируем функцию showToast
    window.showToast = showToastNotification;

    // Экспортируем типы ошибок для использования в других модулях
    window.ErrorTypes = ErrorTypes;
    window.ErrorSeverity = ErrorSeverity;
})();

