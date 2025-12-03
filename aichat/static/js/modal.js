/**
 * Универсальная система модальных окон
 * Замена для alert(), confirm() и prompt()
 */

(function() {
    'use strict';

    // Типы модальных окон
    const ModalType = {
        INFO: 'info',
        SUCCESS: 'success',
        ERROR: 'error',
        WARNING: 'warning',
        CONFIRM: 'confirm'
    };

    /**
     * Создает и показывает модальное окно
     */
    function createModal(options = {}) {
        const {
            title = '',
            message = '',
            type = ModalType.INFO,
            confirmText = 'ОК',
            cancelText = 'Отмена',
            onConfirm = null,
            onCancel = null,
            showCancel = type === ModalType.CONFIRM,
            html = false,
            width = 'auto',
            maxWidth = '500px'
        } = options;

        // Создаем overlay
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.style.display = 'flex';

        // Создаем модальное окно
        const modal = document.createElement('div');
        modal.className = `modal-dialog modal-${type}`;
        modal.style.maxWidth = maxWidth;
        if (width !== 'auto') {
            modal.style.width = width;
        }

        // Иконки для разных типов
        const icons = {
            [ModalType.INFO]: 'ℹ️',
            [ModalType.SUCCESS]: '✅',
            [ModalType.ERROR]: '❌',
            [ModalType.WARNING]: '⚠️',
            [ModalType.CONFIRM]: '❓'
        };

        // Цвета для разных типов
        const colors = {
            [ModalType.INFO]: '#2196f3',
            [ModalType.SUCCESS]: '#4caf50',
            [ModalType.ERROR]: '#c01117',
            [ModalType.WARNING]: '#ff9800',
            [ModalType.CONFIRM]: '#2196f3'
        };

        const icon = icons[type] || icons[ModalType.INFO];
        const color = colors[type] || colors[ModalType.INFO];

        // Создаем содержимое
        modal.innerHTML = `
            <div class="modal-header" style="border-bottom-color: ${color}">
                <div class="modal-icon" style="background-color: ${color}20; color: ${color}">
                    <span style="font-size: 32px;">${icon}</span>
                </div>
                ${title ? `<h3 class="modal-title">${title}</h3>` : ''}
            </div>
            <div class="modal-body">
                ${html ? message : `<p class="modal-message">${message}</p>`}
            </div>
            <div class="modal-footer">
                ${showCancel ? `
                    <button class="modal-btn modal-btn-cancel" data-action="cancel">
                        ${cancelText}
                    </button>
                ` : ''}
                <button class="modal-btn modal-btn-confirm" data-action="confirm" style="background-color: ${color}">
                    ${confirmText}
                </button>
            </div>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        // Анимация появления
        requestAnimationFrame(() => {
            overlay.classList.add('modal-show');
            modal.classList.add('modal-show');
        });

        // Функция закрытия
        const close = (result) => {
            overlay.classList.remove('modal-show');
            modal.classList.remove('modal-show');
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
            }, 300);
            return result;
        };

        // Обработчики событий
        const handleConfirm = () => {
            if (onConfirm) {
                const result = onConfirm();
                if (result !== false) {
                    close(true);
                }
            } else {
                close(true);
            }
        };

        const handleCancel = () => {
            if (onCancel) {
                onCancel();
            }
            close(false);
        };

        // Назначаем обработчики
        modal.querySelector('[data-action="confirm"]').addEventListener('click', handleConfirm);
        if (showCancel) {
            modal.querySelector('[data-action="cancel"]').addEventListener('click', handleCancel);
        }

        // Закрытие по клику на overlay
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                if (type === ModalType.CONFIRM) {
                    handleCancel();
                } else {
                    handleConfirm();
                }
            }
        });

        // Закрытие по Escape
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                if (type === ModalType.CONFIRM) {
                    handleCancel();
                } else {
                    handleConfirm();
                }
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

        // Фокус на кнопке подтверждения
        const confirmBtn = modal.querySelector('[data-action="confirm"]');
        if (confirmBtn) {
            setTimeout(() => confirmBtn.focus(), 100);
        }

        return {
            close: () => close(false),
            element: modal,
            overlay: overlay
        };
    }

    /**
     * Показывает информационное модальное окно (замена alert)
     */
    window.showModal = function(message, title = '', type = ModalType.INFO) {
        return new Promise((resolve) => {
            createModal({
                title: title,
                message: message,
                type: type,
                onConfirm: () => {
                    resolve(true);
                }
            });
        });
    };

    /**
     * Показывает модальное окно подтверждения (замена confirm)
     */
    window.showConfirm = function(message, title = 'Подтверждение') {
        return new Promise((resolve) => {
            createModal({
                title: title,
                message: message,
                type: ModalType.CONFIRM,
                showCancel: true,
                onConfirm: () => {
                    resolve(true);
                },
                onCancel: () => {
                    resolve(false);
                }
            });
        });
    };

    /**
     * Показывает модальное окно успеха
     */
    window.showSuccess = function(message, title = 'Успешно') {
        return showModal(message, title, ModalType.SUCCESS);
    };

    /**
     * Показывает модальное окно ошибки
     */
    window.showError = function(message, title = 'Ошибка') {
        return showModal(message, title, ModalType.ERROR);
    };

    /**
     * Показывает модальное окно предупреждения
     */
    window.showWarning = function(message, title = 'Внимание') {
        return showModal(message, title, ModalType.WARNING);
    };

    /**
     * Показывает информационное модальное окно
     */
    window.showInfo = function(message, title = 'Информация') {
        return showModal(message, title, ModalType.INFO);
    };

    /**
     * Замена для alert() - для обратной совместимости
     */
    window.alert = function(message) {
        return showModal(message, 'Уведомление', ModalType.INFO);
    };

    /**
     * Замена для confirm() - для обратной совместимости
     */
    window.confirm = function(message) {
        return showConfirm(message, 'Подтверждение');
    };

    // Экспортируем типы
    window.ModalType = ModalType;
})();

