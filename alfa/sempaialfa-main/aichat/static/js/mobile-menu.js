/**
 * Мобильное меню (Гамбургер и Drawer)
 * Управление выдвижным меню для мобильных устройств
 */

(function() {
    'use strict';
    
    // Инициализация при загрузке DOM
    document.addEventListener('DOMContentLoaded', function() {
        initMobileMenu();
    });
    
    function initMobileMenu() {
        // Создаем кнопку-гамбургер, если её нет
        const header = document.querySelector('.index-header-container, .cabinet-header-top');
        if (!header) return;
        
        const existingToggle = header.querySelector('.mobile-menu-toggle');
        if (!existingToggle && window.innerWidth <= 768) {
            createMobileMenuToggle(header);
        }
        
        // Создаем drawer-меню, если его нет
        const existingDrawer = document.querySelector('.mobile-menu-drawer');
        if (!existingDrawer && window.innerWidth <= 768) {
            createMobileMenuDrawer();
        }
        
        // Обработка изменения размера окна
        let resizeTimer;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                if (window.innerWidth > 768) {
                    closeMobileMenu();
                }
            }, 250);
        });
        
        // Закрытие меню при клике на overlay
        const overlay = document.querySelector('.mobile-menu-drawer-overlay');
        if (overlay) {
            overlay.addEventListener('click', closeMobileMenu);
        }
        
        // Закрытие меню при клике на ссылку
        const drawerLinks = document.querySelectorAll('.mobile-menu-drawer .index-nav-link');
        drawerLinks.forEach(link => {
            link.addEventListener('click', function() {
                setTimeout(closeMobileMenu, 300); // Небольшая задержка для плавности
            });
        });
    }
    
    function createMobileMenuToggle(header) {
        // Проверяем, есть ли уже кнопка
        if (header.querySelector('.mobile-menu-toggle')) return;
        
        const toggle = document.createElement('button');
        toggle.className = 'mobile-menu-toggle';
        toggle.setAttribute('aria-label', 'Открыть меню');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.innerHTML = '<span></span><span></span><span></span>';
        toggle.addEventListener('click', toggleMobileMenu);
        
        // Вставляем перед логотипом или в начало header-actions
        const logo = header.querySelector('.index-logo, .cabinet-logo-section');
        if (logo) {
            header.insertBefore(toggle, logo);
        } else {
            header.insertBefore(toggle, header.firstChild);
        }
    }
    
    function createMobileMenuDrawer() {
        // Проверяем, есть ли уже drawer
        if (document.querySelector('.mobile-menu-drawer')) return;
        
        const nav = document.querySelector('.index-nav');
        if (!nav) return;
        
        // Создаем overlay для затемнения фона
        const overlay = document.createElement('div');
        overlay.className = 'mobile-menu-drawer-overlay';
        document.body.appendChild(overlay);
        
        // Создаем drawer-контейнер
        const drawer = document.createElement('div');
        drawer.className = 'mobile-menu-drawer';
        
        // Копируем навигацию
        const navClone = nav.cloneNode(true);
        drawer.appendChild(navClone);
        
        document.body.appendChild(drawer);
    }
    
    function toggleMobileMenu() {
        const toggle = document.querySelector('.mobile-menu-toggle');
        const drawer = document.querySelector('.mobile-menu-drawer');
        const overlay = document.querySelector('.mobile-menu-drawer-overlay');
        
        if (!toggle || !drawer) return;
        
        const isActive = toggle.classList.contains('active');
        
        if (isActive) {
            closeMobileMenu();
        } else {
            openMobileMenu();
        }
    }
    
    function openMobileMenu() {
        const toggle = document.querySelector('.mobile-menu-toggle');
        const drawer = document.querySelector('.mobile-menu-drawer');
        const overlay = document.querySelector('.mobile-menu-drawer-overlay');
        
        if (toggle) {
            toggle.classList.add('active');
            toggle.setAttribute('aria-expanded', 'true');
        }
        
        if (drawer) {
            drawer.classList.add('active');
        }
        
        if (overlay) {
            overlay.classList.add('active');
        }
        
        // Блокируем прокрутку body
        document.body.style.overflow = 'hidden';
    }
    
    function closeMobileMenu() {
        const toggle = document.querySelector('.mobile-menu-toggle');
        const drawer = document.querySelector('.mobile-menu-drawer');
        const overlay = document.querySelector('.mobile-menu-drawer-overlay');
        
        if (toggle) {
            toggle.classList.remove('active');
            toggle.setAttribute('aria-expanded', 'false');
        }
        
        if (drawer) {
            drawer.classList.remove('active');
        }
        
        if (overlay) {
            overlay.classList.remove('active');
        }
        
        // Разблокируем прокрутку body
        document.body.style.overflow = '';
    }
    
    // Экспортируем функции для глобального доступа
    window.toggleMobileMenu = toggleMobileMenu;
    window.openMobileMenu = openMobileMenu;
    window.closeMobileMenu = closeMobileMenu;
    
    // Закрытие меню при нажатии Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeMobileMenu();
        }
    });
})();

