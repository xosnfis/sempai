/**
 * Система визуализации данных для Альфа-Ассистент
 * Использует Chart.js для создания графиков и диаграмм
 */

// Глобальная переменная для хранения загруженных графиков
let chartInstances = new Map();
let chartJsLoaded = false;

// Цветовая схема проекта
const CHART_COLORS = {
    primary: '#ff3333',
    primaryLight: '#ff6666',
    primaryLighter: '#ff9999',
    background: '#f8f8f8',
    backgroundDark: '#363636',
    text: '#000000',
    textDark: '#e0e0e0',
    grid: 'rgba(0, 0, 0, 0.1)',
    gridDark: 'rgba(255, 255, 255, 0.1)'
};

// Палитра цветов для круговых диаграмм
const CHART_PALETTE = [
    '#ff3333', '#ff6666', '#ff9999', '#ffcccc',
    '#ff5733', '#ff8c66', '#ffb399', '#ffd9cc',
    '#cc3333', '#cc6666', '#cc9999', '#cccccc'
];

/**
 * Ленивая загрузка Chart.js
 */
function loadChartJS() {
    return new Promise((resolve, reject) => {
        if (chartJsLoaded || typeof Chart !== 'undefined') {
            chartJsLoaded = true;
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
        script.onload = () => {
            chartJsLoaded = true;
            resolve();
        };
        script.onerror = () => {
            reject(new Error('Не удалось загрузить Chart.js'));
        };
        document.head.appendChild(script);
    });
}

/**
 * Проверка темной темы
 */
function isDarkTheme() {
    return document.body.classList.contains('dark-theme');
}

/**
 * Получение цветов в зависимости от темы
 */
function getThemeColors() {
    const dark = isDarkTheme();
    return {
        background: dark ? CHART_COLORS.backgroundDark : CHART_COLORS.background,
        text: dark ? CHART_COLORS.textDark : CHART_COLORS.text,
        grid: dark ? CHART_COLORS.gridDark : CHART_COLORS.grid
    };
}

/**
 * Создание градиента для заливки
 */
function createGradient(ctx, colorStart, colorEnd, opacity = 1) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    
    // Конвертируем hex в rgba
    function hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    
    gradient.addColorStop(0, hexToRgba(colorStart, opacity));
    gradient.addColorStop(1, hexToRgba(colorEnd, 0));
    return gradient;
}

/**
 * Основная функция рендеринга графиков
 */
async function renderChart(chartType, data, containerId, options = {}) {
    try {
        // Валидация входных данных
        if (!data) {
            throw new Error('Данные для графика не предоставлены');
        }
        
        if (!data.labels || !Array.isArray(data.labels) || data.labels.length === 0) {
            throw new Error('Отсутствуют или некорректны метки (labels) для графика');
        }
        
        if (!data.data || !Array.isArray(data.data) || data.data.length === 0) {
            throw new Error('Отсутствуют или некорректны данные (data) для графика');
        }
        
        if (data.labels.length !== data.data.length) {
            console.warn(`Несоответствие длин: labels (${data.labels.length}) != data (${data.data.length}). Обрезаем до минимальной длины.`);
            const minLength = Math.min(data.labels.length, data.data.length);
            data.labels = data.labels.slice(0, minLength);
            data.data = data.data.slice(0, minLength);
        }
        
        // Фильтруем некорректные значения
        data.data = data.data.map(val => {
            const num = typeof val === 'string' ? parseFloat(val) : val;
            return isNaN(num) ? 0 : num;
        });
        
        // Загружаем Chart.js если еще не загружен
        await loadChartJS();

        // Получаем контейнер
        let container = document.getElementById(containerId);
        if (!container) {
            container = document.createElement('div');
            container.id = containerId;
            container.className = 'chart-container';
            // Если контейнер не найден, создаем временный
            console.warn(`Контейнер ${containerId} не найден, создан временный`);
        }

        // Создаем canvas если его нет
        let canvas = container.querySelector('canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.style.maxWidth = '100%';
            canvas.style.height = 'auto';
            container.appendChild(canvas);
        }

        // Удаляем старый график если есть
        const oldChart = chartInstances.get(containerId);
        if (oldChart) {
            oldChart.destroy();
        }

        // Получаем контекст (будет использован позже для градиентов)
        const ctx = canvas.getContext('2d');
        const themeColors = getThemeColors();

        // Базовые настройки
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: true,
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            },
            plugins: {
                legend: {
                    display: options.showLegend !== false,
                    position: options.legendPosition || 'top',
                    labels: {
                        color: themeColors.text,
                        font: {
                            family: 'Inter, Manrope, sans-serif',
                            size: 12
                        },
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: themeColors.background,
                    titleColor: themeColors.text,
                    bodyColor: themeColors.text,
                    borderColor: CHART_COLORS.primary,
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('ru-RU').format(context.parsed.y) + ' ₽';
                            } else if (context.parsed !== null) {
                                label += new Intl.NumberFormat('ru-RU').format(context.parsed) + ' ₽';
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {}
        };

        // Специфичные настройки для каждого типа графика
        let chartConfig = {};

        switch (chartType.toLowerCase()) {
            case 'line':
                chartConfig = createLineChart(data, themeColors, options, ctx);
                break;
            case 'bar':
                chartConfig = createBarChart(data, themeColors, options, ctx);
                break;
            case 'pie':
                chartConfig = createPieChart(data, themeColors, options);
                break;
            case 'doughnut':
                chartConfig = createDoughnutChart(data, themeColors, options);
                break;
            case 'horizontal':
            case 'barhorizontal':
                chartConfig = createHorizontalBarChart(data, themeColors, options, ctx);
                break;
            default:
                throw new Error(`Неизвестный тип графика: ${chartType}`);
        }

        // Объединяем настройки
        const finalConfig = {
            type: chartConfig.type,
            data: chartConfig.data,
            options: { ...defaultOptions, ...chartConfig.options }
        };

        // Создаем график (используем реальный контекст canvas)
        const chart = new Chart(canvas, finalConfig);
        chartInstances.set(containerId, chart);

        // Добавляем кнопку экспорта
        addExportButton(container, canvas, containerId);

        return chart;
    } catch (error) {
        console.error('Ошибка при создании графика:', error);
        throw error;
    }
}

/**
 * Создание линейного графика
 */
function createLineChart(data, themeColors, options, chartCtx) {
    // Функция для создания градиента (будет вызвана после инициализации canvas)
    function getGradient(ctx) {
        if (!ctx) return `rgba(255, 51, 51, 0.3)`;
        return createGradient(ctx, CHART_COLORS.primary, CHART_COLORS.primaryLight, 0.3);
    }

    return {
        type: 'line',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: data.label || 'Данные',
                data: data.data || [],
                borderColor: CHART_COLORS.primary,
                backgroundColor: function(context) {
                    const chart = context.chart;
                    const ctx = chart.ctx;
                    const gradient = ctx.createLinearGradient(0, chart.chartArea.top, 0, chart.chartArea.bottom);
                    gradient.addColorStop(0, 'rgba(255, 51, 51, 0.3)');
                    gradient.addColorStop(1, 'rgba(255, 51, 51, 0)');
                    return gradient;
                },
                borderWidth: 3,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBackgroundColor: CHART_COLORS.primary,
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                fill: true,
                tension: 0.4,
                cubicInterpolationMode: 'monotone'
            }]
        },
        options: {
            scales: {
                x: {
                    grid: {
                        color: themeColors.grid,
                        drawBorder: false
                    },
                    ticks: {
                        color: themeColors.text,
                        font: {
                            family: 'Inter, Manrope, sans-serif',
                            size: 11
                        }
                    }
                },
                y: {
                    grid: {
                        color: themeColors.grid,
                        drawBorder: false
                    },
                    ticks: {
                        color: themeColors.text,
                        font: {
                            family: 'Inter, Manrope, sans-serif',
                            size: 11
                        },
                        callback: function(value) {
                            return new Intl.NumberFormat('ru-RU').format(value) + ' ₽';
                        }
                    }
                }
            }
        }
    };
}

/**
 * Создание столбчатой диаграммы
 */
function createBarChart(data, themeColors, options, chartCtx) {
    // Используем массив цветов для столбцов
    const backgroundColor = Array.isArray(data.data) && data.data.length > 0 
        ? data.data.map((_, i) => {
            const alpha = 0.7 + (i % 3) * 0.1;
            const r = parseInt(CHART_COLORS.primary.slice(1, 3), 16);
            const g = parseInt(CHART_COLORS.primary.slice(3, 5), 16);
            const b = parseInt(CHART_COLORS.primary.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        })
        : CHART_COLORS.primary;

    return {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: data.label || 'Данные',
                data: data.data || [],
                backgroundColor: backgroundColor,
                borderColor: CHART_COLORS.primary,
                borderWidth: 1,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: themeColors.text,
                        font: {
                            family: 'Inter, Manrope, sans-serif',
                            size: 11
                        }
                    }
                },
                y: {
                    grid: {
                        color: themeColors.grid,
                        drawBorder: false
                    },
                    ticks: {
                        color: themeColors.text,
                        font: {
                            family: 'Inter, Manrope, sans-serif',
                            size: 11
                        },
                        callback: function(value) {
                            return new Intl.NumberFormat('ru-RU').format(value) + ' ₽';
                        }
                    }
                }
            },
            barPercentage: 0.6,
            categoryPercentage: 0.6
        }
    };
}

/**
 * Создание горизонтальной столбчатой диаграммы
 */
function createHorizontalBarChart(data, themeColors, options, chartCtx) {
    // Используем градиент для горизонтальных столбцов
    const backgroundColor = function(context) {
        const chart = context.chart;
        const ctx = chart.ctx;
        const gradient = ctx.createLinearGradient(chart.chartArea.left, 0, chart.chartArea.right, 0);
        gradient.addColorStop(0, CHART_COLORS.primary);
        gradient.addColorStop(1, CHART_COLORS.primaryLight);
        return gradient;
    };

    return {
        type: 'bar',
        data: {
            labels: data.labels || [],
            datasets: [{
                label: data.label || 'Данные',
                data: data.data || [],
                backgroundColor: backgroundColor,
                borderColor: CHART_COLORS.primary,
                borderWidth: 1,
                borderRadius: 8
            }]
        },
        options: {
            indexAxis: 'y',
            scales: {
                x: {
                    grid: {
                        color: themeColors.grid,
                        drawBorder: false
                    },
                    ticks: {
                        color: themeColors.text,
                        font: {
                            family: 'Inter, Manrope, sans-serif',
                            size: 11
                        },
                        callback: function(value) {
                            return new Intl.NumberFormat('ru-RU').format(value) + ' ₽';
                        }
                    }
                },
                y: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: themeColors.text,
                        font: {
                            family: 'Inter, Manrope, sans-serif',
                            size: 11
                        }
                    }
                }
            }
        }
    };
}

/**
 * Создание круговой диаграммы
 */
function createPieChart(data, themeColors, options) {
    const colors = data.colors || CHART_PALETTE.slice(0, data.labels?.length || 10);

    return {
        type: 'pie',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.data || [],
                backgroundColor: colors,
                borderColor: isDarkTheme() ? CHART_COLORS.backgroundDark : '#ffffff',
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${new Intl.NumberFormat('ru-RU').format(value)} ₽ (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };
}

/**
 * Создание кольцевой диаграммы
 */
function createDoughnutChart(data, themeColors, options) {
    const colors = data.colors || CHART_PALETTE.slice(0, data.labels?.length || 10);

    return {
        type: 'doughnut',
        data: {
            labels: data.labels || [],
            datasets: [{
                data: data.data || [],
                backgroundColor: colors,
                borderColor: isDarkTheme() ? CHART_COLORS.backgroundDark : '#ffffff',
                borderWidth: 2,
                hoverOffset: 4
            }]
        },
        options: {
            cutout: '60%',
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${new Intl.NumberFormat('ru-RU').format(value)} ₽ (${percentage}%)`;
                        }
                    }
                }
            }
        }
    };
}

/**
 * Добавление кнопки экспорта графика
 */
function addExportButton(container, canvas, containerId) {
    // Удаляем старую кнопку если есть
    const oldButton = container.querySelector('.chart-export-btn');
    if (oldButton) {
        oldButton.remove();
    }

    const exportBtn = document.createElement('button');
    exportBtn.className = 'chart-export-btn';
    exportBtn.title = 'Сохранить график';
    exportBtn.innerHTML = '💾';
    exportBtn.onclick = () => {
        const url = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = `chart_${containerId}_${Date.now()}.png`;
        link.href = url;
        link.click();
    };
    container.appendChild(exportBtn);
}

/**
 * Обработка команды [CHART:тип:данные_json]
 */
function processChartCommand(command) {
    const match = command.match(/\[CHART:(\w+):(.+)\]/);
    if (!match) return null;

    const chartType = match[1];
    let chartData;
    try {
        chartData = JSON.parse(match[2]);
    } catch (e) {
        console.error('Ошибка парсинга данных графика:', e);
        return null;
    }

    return { type: chartType, data: chartData };
}

/**
 * Функции-хелперы для каждого типа данных
 */

/**
 * График расходов/доходов по времени (чеки)
 */
function renderReceiptsChart(receipts, chartType = 'line') {
    if (!receipts || receipts.length === 0) {
        throw new Error('Нет данных о чеках');
    }

    // Группируем по датам
    const grouped = {};
    receipts.forEach(receipt => {
        const date = receipt.date ? receipt.date.split('T')[0] : 'Неизвестно';
        if (!grouped[date]) {
            grouped[date] = { income: 0, expense: 0 };
        }
        const amount = receipt.amount || 0;
        if (receipt.operationType === 'Доход' || receipt.operationType === 'Приход') {
            grouped[date].income += amount;
        } else {
            grouped[date].expense += amount;
        }
    });

    const dates = Object.keys(grouped).sort();
    const incomeData = dates.map(date => grouped[date].income);
    const expenseData = dates.map(date => grouped[date].expense);

    const containerId = `chart_receipts_${Date.now()}`;
    const container = document.createElement('div');
    container.id = containerId;
    container.className = 'chart-container';

    if (chartType === 'line') {
        // Линейный график с двумя линиями
        return renderChart('line', {
            labels: dates,
            datasets: [
                {
                    label: 'Доходы',
                    data: incomeData,
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)'
                },
                {
                    label: 'Расходы',
                    data: expenseData,
                    borderColor: CHART_COLORS.primary,
                    backgroundColor: 'rgba(255, 51, 51, 0.1)'
                }
            ]
        }, containerId);
    } else {
        // Столбчатая диаграмма
        return renderChart('bar', {
            labels: dates,
            data: expenseData,
            label: 'Расходы'
        }, containerId);
    }
}

/**
 * График инвентаризации по категориям
 */
function renderInventoryChart(inventory, chartType = 'doughnut') {
    if (!inventory || inventory.length === 0) {
        throw new Error('Нет данных об инвентаризации');
    }

    const categories = {};
    inventory.forEach(item => {
        const category = item.folder || item.folderId || 'Без категории';
        if (!categories[category]) {
            categories[category] = { count: 0, value: 0 };
        }
        categories[category].count += item.quantity || 0;
        categories[category].value += (item.quantity || 0) * (item.price || 0);
    });

    const labels = Object.keys(categories);
    const data = labels.map(cat => categories[cat].value);

    const containerId = `chart_inventory_${Date.now()}`;
    const container = document.createElement('div');
    container.id = containerId;
    container.className = 'chart-container';

    return renderChart(chartType, {
        labels: labels,
        data: data
    }, containerId);
}

/**
 * График зарплат сотрудников
 */
function renderEmployeesChart(employees, chartType = 'bar') {
    if (!employees || employees.length === 0) {
        throw new Error('Нет данных о сотрудниках');
    }

    const labels = employees.map(emp => emp.fio || 'Не указано');
    const data = employees.map(emp => emp.salary || 0);

    const containerId = `chart_employees_${Date.now()}`;
    const container = document.createElement('div');
    container.id = containerId;
    container.className = 'chart-container';

    if (chartType === 'horizontal') {
        return renderChart('horizontal', {
            labels: labels,
            data: data,
            label: 'Зарплата'
        }, containerId);
    } else {
        return renderChart('bar', {
            labels: labels,
            data: data,
            label: 'Зарплата'
        }, containerId);
    }
}

/**
 * График задолженностей по налогам
 */
function renderTaxesChart(taxesData, chartType = 'pie') {
    if (!taxesData || Object.keys(taxesData).length === 0) {
        throw new Error('Нет данных о налогах');
    }

    const taxNames = {
        profit: 'Налог на прибыль',
        vat: 'НДС',
        property: 'Налог на имущество',
        insurance: 'Страховые взносы'
    };

    const labels = [];
    const data = [];

    Object.keys(taxesData).forEach(key => {
        const debt = taxesData[key]?.debt || 0;
        if (debt > 0) {
            labels.push(taxNames[key] || key);
            data.push(debt);
        }
    });

    if (data.length === 0) {
        throw new Error('Нет задолженностей по налогам');
    }

    const containerId = `chart_taxes_${Date.now()}`;
    const container = document.createElement('div');
    container.id = containerId;
    container.className = 'chart-container';

    return renderChart(chartType, {
        labels: labels,
        data: data
    }, containerId);
}

/**
 * График задолженностей по коммунальным услугам
 */
function renderUtilitiesChart(utilitiesData, chartType = 'pie') {
    if (!utilitiesData || Object.keys(utilitiesData).length === 0) {
        throw new Error('Нет данных о коммунальных услугах');
    }

    const utilNames = {
        electricity: 'Электричество',
        water: 'Водоснабжение',
        heating: 'Отопление',
        waste: 'Вывоз ТКО',
        security: 'Охранные услуги',
        internet: 'Интернет'
    };

    const labels = [];
    const data = [];

    Object.keys(utilitiesData).forEach(key => {
        const debt = utilitiesData[key]?.debt || 0;
        if (debt > 0) {
            labels.push(utilNames[key] || key);
            data.push(debt);
        }
    });

    if (data.length === 0) {
        throw new Error('Нет задолженностей по коммунальным услугам');
    }

    const containerId = `chart_utilities_${Date.now()}`;
    const container = document.createElement('div');
    container.id = containerId;
    container.className = 'chart-container';

    return renderChart(chartType, {
        labels: labels,
        data: data
    }, containerId);
}

/**
 * График сравнения балансов счетов
 */
function renderBalanceChart(balance1, balance2) {
    const containerId = `chart_balance_${Date.now()}`;
    const container = document.createElement('div');
    container.id = containerId;
    container.className = 'chart-container';

    return renderChart('bar', {
        labels: ['Счет 1', 'Счет 2', 'Общий баланс'],
        data: [balance1 || 0, balance2 || 0, (balance1 || 0) + (balance2 || 0)],
        label: 'Баланс'
    }, containerId);
}

/**
 * Очистка всех графиков
 */
function destroyAllCharts() {
    chartInstances.forEach((chart, id) => {
        chart.destroy();
    });
    chartInstances.clear();
}

// Экспорт функций для глобального использования
window.renderChart = renderChart;
window.processChartCommand = processChartCommand;
window.renderReceiptsChart = renderReceiptsChart;
window.renderInventoryChart = renderInventoryChart;
window.renderEmployeesChart = renderEmployeesChart;
window.renderTaxesChart = renderTaxesChart;
window.renderUtilitiesChart = renderUtilitiesChart;
window.renderBalanceChart = renderBalanceChart;
window.destroyAllCharts = destroyAllCharts;

