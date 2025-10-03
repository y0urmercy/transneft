#!/usr/bin/env python3
"""
Универсальный запуск всей системы (бэкенд + фронтенд)
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path

def run_backend():
    """Запуск бэкенда в отдельном потоке"""
    try:
        print("🔧 Запуск бэкенда...")
        subprocess.run([sys.executable, "run_backend.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка бэкенда: {e}")

def run_frontend():
    """Запуск фронтенда в отдельном потоке"""
    try:
        print("🎨 Запуск фронтенда...")
        if os.name == 'nt':  # Windows
            subprocess.run(["npm", "run", "dev"], cwd="frontend", shell=True, check=True)
        else:  # Linux/Mac
            subprocess.run(["./run_frontend.sh"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка фронтенда: {e}")

def main():
    print("🚀 Transneft RAG System - Запуск всей системы")
    print("=" * 50)
    
    # Проверяем существование необходимых файлов
    if not Path("run_backend.py").exists():
        print("❌ run_backend.py не найден!")
        return
    
    if not Path("frontend").exists():
        print("❌ Папка frontend не найдена!")
        return
    
    # Запускаем в отдельных потоках
    backend_thread = threading.Thread(target=run_backend)
    frontend_thread = threading.Thread(target=run_frontend)
    
    backend_thread.daemon = True
    frontend_thread.daemon = True
    
    backend_thread.start()
    time.sleep(3)  # Даем бэкенду время на запуск
    
    frontend_thread.start()
    
    print("\n✅ Система запускается...")
    print("🌐 Фронтенд: http://localhost:3000")
    print("🔧 Бэкенд:   http://localhost:8000")
    print("📚 Документация API: http://localhost:8000/docs")
    print("\n⏹️  Для остановки нажмите Ctrl+C")
    
    try:
        # Держим основной поток активным
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановка системы...")

if __name__ == "__main__":
    main()