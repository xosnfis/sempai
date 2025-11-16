#!/usr/bin/env python
"""
Скрипт для проверки подключения к LM Studio
Использование: python check_lm_studio.py
"""

import requests
import sys
import json
from urllib.parse import urlparse

def check_lm_studio(url='http://localhost:1234/v1/chat/completions'):
    """Проверяет подключение к LM Studio"""
    print("=" * 60)
    print("Проверка подключения к LM Studio")
    print("=" * 60)
    print(f"\nURL: {url}")
    print()
    
    # Проверка 1: Доступность сервера
    print("1. Проверка доступности сервера...")
    try:
        # Пробуем простой GET запрос к корню сервера
        base_url = url.rsplit('/v1/', 1)[0]
        response = requests.get(base_url, timeout=5)
        print(f"   ✓ Сервер доступен (статус: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("   ✗ ОШИБКА: Не удалось подключиться к серверу")
        print("   → Убедитесь, что LM Studio запущен")
        print("   → Проверьте, что сервер активен (Status: Running в LM Studio)")
        print("   → Проверьте, что порт 1234 не занят другим приложением")
        return False
    except requests.exceptions.Timeout:
        print("   ✗ ОШИБКА: Превышено время ожидания")
        return False
    except Exception as e:
        print(f"   ⚠ Предупреждение: {str(e)}")
    
    # Проверка 2: Доступность API endpoint
    print("\n2. Проверка API endpoint...")
    try:
        # Пробуем простой запрос к API
        test_payload = {
            "model": "test",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1
        }
        response = requests.post(url, json=test_payload, timeout=10)
        print(f"   ✓ API endpoint доступен (статус: {response.status_code})")
        
        if response.status_code == 404:
            print("   ⚠ Endpoint не найден. Проверьте URL.")
            return False
        elif response.status_code == 400:
            # Это нормально - модель может не существовать, но сервер работает
            print("   ✓ Сервер отвечает (ошибка 400 ожидаема для тестового запроса)")
        elif response.status_code == 200:
            print("   ✓ Сервер работает корректно!")
    except requests.exceptions.ConnectionError:
        print("   ✗ ОШИБКА: Не удалось подключиться к API")
        return False
    except requests.exceptions.Timeout:
        print("   ✗ ОШИБКА: Превышено время ожидания ответа")
        return False
    except Exception as e:
        print(f"   ✗ ОШИБКА: {str(e)}")
        return False
    
    # Проверка 3: Проверка с реальной моделью
    print("\n3. Проверка с моделью 'qwen3-vl-4b'...")
    try:
        test_payload = {
            "model": "qwen3-vl-4b",
            "messages": [{"role": "user", "content": "Привет"}],
            "max_tokens": 10,
            "temperature": 0.7
        }
        response = requests.post(url, json=test_payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✓ Модель 'qwen3-vl-4b' работает!")
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0].get('message', {}).get('content', '')
                print(f"   ✓ Получен ответ от модели: {content[:50]}...")
        elif response.status_code == 404:
            print("   ✗ ОШИБКА: Модель 'qwen3-vl-4b' не найдена")
            print("   → Убедитесь, что модель загружена в LM Studio")
            print("   → Проверьте, что модель активна (Status: READY)")
            return False
        else:
            print(f"   ⚠ Статус ответа: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Детали: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   Ответ сервера: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print("   ✗ ОШИБКА: Не удалось подключиться")
        return False
    except requests.exceptions.Timeout:
        print("   ✗ ОШИБКА: Превышено время ожидания (модель может быть слишком медленной)")
        print("   → Попробуйте использовать более легкую модель")
        return False
    except Exception as e:
        print(f"   ✗ ОШИБКА: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ Все проверки пройдены! LM Studio готов к работе.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    # Можно указать другой URL через аргумент командной строки
    url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:1234/v1/chat/completions'
    
    success = check_lm_studio(url)
    sys.exit(0 if success else 1)

