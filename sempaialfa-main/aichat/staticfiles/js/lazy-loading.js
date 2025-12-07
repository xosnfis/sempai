/**
 * Продвинутый Lazy Loading для изображений
 * Использует Intersection Observer API для оптимальной производительности
 */

(function() {
    'use strict';

    // Проверяем поддержку Intersection Observer
    if ('IntersectionObserver' in window) {
        // Создаем observer с настройками
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    
                    // Проверяем наличие data-src (для продвинутого lazy loading)
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    
                    // Проверяем наличие data-srcset
                    if (img.dataset.srcset) {
                        img.srcset = img.dataset.srcset;
                        img.removeAttribute('data-srcset');
                    }
                    
                    // Убираем класс lazy-loading после загрузки
                    img.classList.remove('lazy-loading');
                    img.classList.add('lazy-loaded');
                    
                    // Обработка события загрузки
                    img.addEventListener('load', function() {
                        this.classList.add('lazy-load-complete');
                        this.classList.remove('lazy-loading');
                    });
                    
                    // Обработка ошибок загрузки
                    img.addEventListener('error', function() {
                        this.classList.add('lazy-load-error');
                        this.classList.remove('lazy-loading');
                        // Можно добавить placeholder для ошибок
                        if (!this.hasAttribute('data-error-handled')) {
                            this.setAttribute('data-error-handled', 'true');
                            console.warn('Ошибка загрузки изображения:', this.src || this.dataset.src);
                        }
                    });
                    
                    // Прекращаем наблюдение за этим элементом
                    observer.unobserve(img);
                }
            });
        }, {
            // Загружаем изображения за 50px до того, как они попадут в viewport
            rootMargin: '50px'
        });

        // Находим все изображения с атрибутом loading="lazy" или классом lazy-load
        const lazyImages = document.querySelectorAll('img[loading="lazy"], img.lazy-load, img[data-src]');
        
        lazyImages.forEach(img => {
            // Добавляем класс для стилизации placeholder
            img.classList.add('lazy-loading');
            
            // Если изображение уже загружено (кеш браузера), сразу показываем его
            if (img.complete && img.naturalHeight !== 0) {
                img.classList.remove('lazy-loading');
                img.classList.add('lazy-loaded');
            } else {
                // Начинаем наблюдение
                imageObserver.observe(img);
            }
        });

        // Также обрабатываем изображения, добавленные динамически
        const observeNewImages = () => {
            const newImages = document.querySelectorAll('img[loading="lazy"]:not(.lazy-loading):not(.lazy-loaded), img.lazy-load:not(.lazy-loading):not(.lazy-loaded)');
            newImages.forEach(img => {
                img.classList.add('lazy-loading');
                imageObserver.observe(img);
            });
        };

        // Наблюдаем за изменениями DOM (для динамически добавленных изображений)
        if ('MutationObserver' in window) {
            const mutationObserver = new MutationObserver(observeNewImages);
            
            // Функция для безопасного запуска observer
            const startObserver = () => {
                if (document.body) {
                    mutationObserver.observe(document.body, {
                        childList: true,
                        subtree: true
                    });
                }
            };
            
            // Запускаем сразу, если body уже загружен, иначе ждем
            if (document.body) {
                startObserver();
            } else {
                document.addEventListener('DOMContentLoaded', startObserver);
            }
        }

        // Также проверяем при загрузке страницы
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', observeNewImages);
        } else {
            observeNewImages();
        }
    } else {
        // Fallback для браузеров без поддержки Intersection Observer
        console.warn('Intersection Observer не поддерживается. Используется стандартный lazy loading браузера.');
        
        // Просто добавляем классы для стилизации
        const lazyImages = document.querySelectorAll('img[loading="lazy"], img.lazy-load');
        lazyImages.forEach(img => {
            img.classList.add('lazy-loaded');
            
            img.addEventListener('load', function() {
                this.classList.add('lazy-load-complete');
            });
            
            img.addEventListener('error', function() {
                this.classList.add('lazy-load-error');
            });
        });
    }

    // Функция для принудительной загрузки изображения (если нужно)
    window.forceLoadImage = function(imgElement) {
        if (imgElement && imgElement.dataset.src) {
            imgElement.src = imgElement.dataset.src;
            imgElement.removeAttribute('data-src');
        }
    };

    // Функция для предзагрузки изображений (если нужно)
    window.preloadImage = function(src) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = reject;
            img.src = src;
        });
    };
})();

