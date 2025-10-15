#!/usr/bin/env python3
import sys
import os
import time


os.system("pip install -r requirements.txt")

if os.path.exists("src"):
    os.chdir("src")
    os.system(f"{sys.executable} main.py")
    
if os.path.exists("frontend"):
    print("🎨 Запускаю фронтенд...")
    os.system('start cmd /k "cd frontend && npm run dev"')
