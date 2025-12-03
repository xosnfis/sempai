/**
 * Универсальная система индикаторов загрузки
 * Использование:
 * - showLoading('Загрузка данных...')
 * - hideLoading()
 * - showButtonLoading(buttonElement)
 * - hideButtonLoading(buttonElement)
 * - showInlineLoading(element, text)
 * - hideInlineLoading(element)
 */

// Глобальный индикатор загрузки (полноэкранный)
let globalLoadingIndicator = null;

/**
 * Инициализация глобального индикатора загрузки
 */
function initGlobalLoadingIndicator() {
    if (!globalLoadingIndicator) {
        globalLoadingIndicator = document.createElement('div');
        globalLoadingIndicator.className = 'loading-indicator';
        globalLoadingIndicator.id = 'globalLoadingIndicator';
        globalLoadingIndicator.innerHTML = `
            <div class="loading-indicator-content">
                <div class="loading-spinner"></div>
                <p class="loading-indicator-text" id="loadingIndicatorText">Загрузка...</p>
            </div>
        `;
        document.body.appendChild(globalLoadingIndicator);
    }
}

/**
 * Показать глобальный индикатор загрузки
 * @param {string} text - Текст сообщения (опционально)
 */
function showLoading(text = 'Загрузка...') {
    initGlobalLoadingIndicator();
    const textElement = document.getElementById('loadingIndicatorText');
    if (textElement) {
        textElement.textContent = text;
    }
    globalLoadingIndicator.classList.add('active');
}

/**
 * Скрыть глобальный индикатор загрузки
 */
function hideLoading() {
    if (globalLoadingIndicator) {
        globalLoadingIndicator.classList.remove('active');
    }
}

/**
 * Показать индикатор загрузки на кнопке
 * @param {HTMLElement} button - Элемент кнопки
 * @param {string} originalText - Оригинальный текст кнопки (сохраняется автоматически)
 */
function showButtonLoading(button, originalText = null) {
    if (!button) return;
    
    // Сохраняем оригинальный текст, если он еще не сохранен
    if (!button.dataset.originalText) {
        button.dataset.originalText = originalText || button.textContent || button.value;
    }
    
    button.classList.add('button-loading');
    button.disabled = true;
    
    // Если это input или button с value
    if (button.tagName === 'INPUT' || button.tagName === 'BUTTON') {
        if (button.type === 'submit' || button.type === 'button') {
            button.style.color = 'transparent';
        }
    }
}

/**
 * Скрыть индикатор загрузки на кнопке
 * @param {HTMLElement} button - Элемент кнопки
 */
function hideButtonLoading(button) {
    if (!button) return;
    
    button.classList.remove('button-loading');
    button.disabled = false;
    
    // Восстанавливаем оригинальный текст
    if (button.dataset.originalText) {
        if (button.tagName === 'INPUT' || button.tagName === 'BUTTON') {
            if (button.type === 'submit' || button.type === 'button') {
                button.value = button.dataset.originalText;
                button.style.color = '';
            } else {
                button.textContent = button.dataset.originalText;
            }
        } else {
            button.textContent = button.dataset.originalText;
        }
        delete button.dataset.originalText;
    }
}

/**
 * Показать инлайн индикатор загрузки
 * @param {HTMLElement} element - Элемент, в который добавить индикатор
 * @param {string} text - Текст сообщения (опционально)
 * @returns {HTMLElement} - Созданный элемент индикатора
 */
function showInlineLoading(element, text = 'Загрузка...') {
    if (!element) return null;
    
    const loadingElement = document.createElement('div');
    loadingElement.className = 'loading-inline';
    loadingElement.innerHTML = `
        <div class="loading-inline-spinner"></div>
        <span>${text}</span>
    `;
    
    element.appendChild(loadingElement);
    return loadingElement;
}

/**
 * Скрыть инлайн индикатор загрузки
 * @param {HTMLElement} loadingElement - Элемент индикатора для удаления
 */
function hideInlineLoading(loadingElement) {
    if (loadingElement && loadingElement.parentNode) {
        loadingElement.parentNode.removeChild(loadingElement);
    }
}

/**
 * Показать индикатор загрузки для секции
 * @param {HTMLElement} section - Элемент секции
 */
function showSectionLoading(section) {
    if (!section) return;
    section.classList.add('section-loading');
}

/**
 * Скрыть индикатор загрузки для секции
 * @param {HTMLElement} section - Элемент секции
 */
function hideSectionLoading(section) {
    if (!section) return;
    section.classList.remove('section-loading');
}

/**
 * Показать индикатор загрузки для таблицы
 * @param {HTMLElement} table - Элемент таблицы
 */
function showTableLoading(table) {
    if (!table) return;
    table.classList.add('table-loading');
}

/**
 * Скрыть индикатор загрузки для таблицы
 * @param {HTMLElement} table - Элемент таблицы
 */
function hideTableLoading(table) {
    if (!table) return;
    table.classList.remove('table-loading');
}

/**
 * Показать индикатор загрузки для формы
 * @param {HTMLElement} form - Элемент формы
 */
function showFormLoading(form) {
    if (!form) return;
    form.classList.add('form-loading');
    
    // Отключаем все поля формы
    const inputs = form.querySelectorAll('input, textarea, select, button');
    inputs.forEach(input => {
        if (!input.dataset.originalDisabled) {
            input.dataset.originalDisabled = input.disabled;
        }
        input.disabled = true;
    });
}

/**
 * Скрыть индикатор загрузки для формы
 * @param {HTMLElement} form - Элемент формы
 */
function hideFormLoading(form) {
    if (!form) return;
    form.classList.remove('form-loading');
    
    // Восстанавливаем состояние полей формы
    const inputs = form.querySelectorAll('input, textarea, select, button');
    inputs.forEach(input => {
        const originalDisabled = input.dataset.originalDisabled === 'true';
        input.disabled = originalDisabled;
        delete input.dataset.originalDisabled;
    });
}

/**
 * Показать индикатор загрузки для модального окна
 * @param {HTMLElement} modal - Элемент модального окна
 */
function showModalLoading(modal) {
    if (!modal) return;
    
    let loadingOverlay = modal.querySelector('.modal-loading');
    if (!loadingOverlay) {
        loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'modal-loading';
        loadingOverlay.innerHTML = '<div class="modal-loading-spinner"></div>';
        modal.appendChild(loadingOverlay);
    }
    loadingOverlay.style.display = 'flex';
}

/**
 * Скрыть индикатор загрузки для модального окна
 * @param {HTMLElement} modal - Элемент модального окна
 */
function hideModalLoading(modal) {
    if (!modal) return;
    
    const loadingOverlay = modal.querySelector('.modal-loading');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

/**
 * Обертка для асинхронных функций с автоматическим показом индикатора загрузки
 * @param {Function} asyncFunction - Асинхронная функция для выполнения
 * @param {Object} options - Опции (text, button, section, etc.)
 * @returns {Promise} - Промис с результатом выполнения функции
 */
async function withLoading(asyncFunction, options = {}) {
    const {
        text = 'Загрузка...',
        button = null,
        section = null,
        form = null,
        modal = null,
        useGlobal = true
    } = options;
    
    try {
        // Показываем соответствующий индикатор
        if (button) {
            showButtonLoading(button);
        } else if (form) {
            showFormLoading(form);
        } else if (section) {
            showSectionLoading(section);
        } else if (modal) {
            showModalLoading(modal);
        } else if (useGlobal) {
            showLoading(text);
        }
        
        // Выполняем функцию
        const result = await asyncFunction();
        
        return result;
    } catch (error) {
        console.error('Ошибка при выполнении операции:', error);
        throw error;
    } finally {
        // Скрываем индикаторы
        if (button) {
            hideButtonLoading(button);
        } else if (form) {
            hideFormLoading(form);
        } else if (section) {
            hideSectionLoading(section);
        } else if (modal) {
            hideModalLoading(modal);
        } else if (useGlobal) {
            hideLoading();
        }
    }
}

/**
 * Создать индикатор загрузки для сообщения чата
 * @param {HTMLElement} messageElement - Элемент сообщения
 * @returns {HTMLElement} - Элемент индикатора
 */
function createChatMessageLoading(messageElement) {
    const loadingElement = document.createElement('div');
    loadingElement.className = 'chat-message-loading';
    loadingElement.innerHTML = `
        <div class="chat-message-loading-spinner"></div>
        <span class="chat-message-loading-text">Думаю...</span>
    `;
    
    if (messageElement) {
        messageElement.appendChild(loadingElement);
    }
    
    return loadingElement;
}

/**
 * Удалить индикатор загрузки сообщения чата
 * @param {HTMLElement} loadingElement - Элемент индикатора
 */
function removeChatMessageLoading(loadingElement) {
    if (loadingElement && loadingElement.parentNode) {
        loadingElement.parentNode.removeChild(loadingElement);
    }
}

// Инициализация при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGlobalLoadingIndicator);
} else {
    initGlobalLoadingIndicator();
}

