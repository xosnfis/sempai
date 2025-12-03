#!/bin/bash
# Bash скрипт для работы с метриками API
# Использование: ./get-metrics.sh [опции]

# Параметры по умолчанию
DAYS=7
CATEGORY=""
METRIC=""
ACTION="summary"
BASE_URL="http://localhost:8000/api/metrics"

# Функция для вывода справки
show_help() {
    cat << EOF
Использование: $0 [опции]

Опции:
    -a, --action ACTION      Действие: summary, calculate, get (по умолчанию: summary)
    -d, --days DAYS          Количество дней (по умолчанию: 7)
    -c, --category CATEGORY  Категория метрики (опционально)
    -m, --metric METRIC      Название метрики (опционально)
    -u, --url URL            Базовый URL API (по умолчанию: http://localhost:8000/api/metrics)
    -h, --help               Показать эту справку

Примеры:
    $0 -a summary -d 7
    $0 -a calculate -d 30
    $0 -a get -d 7 -c performance
    $0 -a get -d 30 -c performance -m response_time_p50
    $0 -u http://130.193.35.191:8000/api/metrics -a summary -d 7

EOF
}

# Парсинг аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -d|--days)
            DAYS="$2"
            shift 2
            ;;
        -c|--category)
            CATEGORY="$2"
            shift 2
            ;;
        -m|--metric)
            METRIC="$2"
            shift 2
            ;;
        -u|--url)
            BASE_URL="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Неизвестный параметр: $1" >&2
            show_help
            exit 1
            ;;
    esac
done

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Функция для получения сводки метрик
get_metrics_summary() {
    local days=$1
    local url="${BASE_URL}/summary/?days=${days}"
    
    echo -e "${CYAN}Getting metrics summary for ${days} days...${NC}"
    echo -e "${GRAY}URL: ${url}${NC}"
    echo ""
    
    local response=$(curl -s -w "\n%{http_code}" "${url}")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        if command -v jq &> /dev/null; then
            echo "$body" | jq '.'
        else
            echo "$body"
            echo ""
            echo -e "${YELLOW}Подсказка: установите 'jq' для красивого вывода JSON (apt-get install jq или yum install jq)${NC}"
        fi
    else
        echo -e "${RED}Ошибка: HTTP ${http_code}${NC}"
        echo "$body"
        return 1
    fi
}

# Функция для расчета метрик
calculate_metrics() {
    local days=$1
    local url="${BASE_URL}/calculate/"
    local body=$(cat <<EOF
{
    "days": ${days}
}
EOF
)
    
    echo -e "${CYAN}Calculating metrics for ${days} days...${NC}"
    echo -e "${GRAY}URL: ${url}${NC}"
    echo ""
    
    local response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "${body}" \
        "${url}")
    local http_code=$(echo "$response" | tail -n1)
    local response_body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        if command -v jq &> /dev/null; then
            echo "$response_body" | jq '.'
        else
            echo "$response_body"
            echo ""
            echo -e "${YELLOW}Подсказка: установите 'jq' для красивого вывода JSON${NC}"
        fi
    else
        echo -e "${RED}Ошибка: HTTP ${http_code}${NC}"
        echo "$response_body"
        return 1
    fi
}

# Функция для получения метрик
get_metrics() {
    local days=$1
    local category=$2
    local metric=$3
    local url="${BASE_URL}/?days=${days}"
    
    if [ -n "$category" ]; then
        url="${url}&category=${category}"
    fi
    if [ -n "$metric" ]; then
        url="${url}&metric=${metric}"
    fi
    
    echo -e "${CYAN}Getting metrics...${NC}"
    echo -e "${GRAY}URL: ${url}${NC}"
    echo ""
    
    local response=$(curl -s -w "\n%{http_code}" "${url}")
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        if command -v jq &> /dev/null; then
            echo "$body" | jq '.'
        else
            echo "$body"
            echo ""
            echo -e "${YELLOW}Подсказка: установите 'jq' для красивого вывода JSON${NC}"
        fi
    else
        echo -e "${RED}Ошибка: HTTP ${http_code}${NC}"
        echo "$body"
        return 1
    fi
}

# Выполнение в зависимости от действия
case "${ACTION,,}" in
    summary)
        get_metrics_summary "$DAYS"
        ;;
    calculate)
        calculate_metrics "$DAYS"
        ;;
    get)
        get_metrics "$DAYS" "$CATEGORY" "$METRIC"
        ;;
    *)
        echo -e "${RED}Unknown action: ${ACTION}${NC}" >&2
        echo -e "${YELLOW}Available actions: summary, calculate, get${NC}"
        exit 1
        ;;
esac
