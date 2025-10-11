#!/usr/bin/env python3
import sys
import os
import time

print("🚀 Запуск Transneft System")

# Установка зависимостей
os.system("pip install -r requirements.txt")

# Запуск бэкенда
print("🔧 Запускаю бэкенд...")
if os.path.exists("src"):
    os.chdir("src")
    os.system(f"{sys.executable} main.py")
    

# Запуск фронтенда в новом окне
if os.path.exists("frontend"):
    print("🎨 Запускаю фронтенд...")
    os.system('start cmd /k "cd frontend && npm run dev"')
