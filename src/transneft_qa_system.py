#!/usr/bin/env python3
"""
Скрипт запуска системы Транснефть QA
"""

import os
import sys

def main():
    """Основная функция запуска"""
    print("🚀 Запуск системы Транснефть QA...")
    
    # Проверка зависимостей
    try:
        import streamlit
        import langchain
        print("✅ Все зависимости установлены")
    except ImportError as e:
        print(f"❌ Отсутствуют зависимости: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return
    
    # Создание необходимых директорий
    directories = ['assets', 'css', 'data', 'results', 'vector_stores']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Создана директория: {directory}")
    
    # Проверка бенчмарка
    benchmark_path = "data/transneft_benchmark.json"
    if not os.path.exists(benchmark_path):
        print(f"❌ Файл бенчмарка не найден: {benchmark_path}")
        print("Поместите transneft_benchmark.json в папку data/")
        return
    
    print("✅ Бенчмарк найден")
    print("🌐 Запуск веб-интерфейса...")
    
    # Запуск Streamlit
    os.system("streamlit run src/transneft_qa_system.py")

if __name__ == "__main__":
    main()