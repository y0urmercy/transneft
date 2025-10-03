#!/usr/bin/env python3
import uvicorn
import os
import sys

if __name__ == "__main__":
    # Добавляем путь к backend
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    sys.path.insert(0, backend_dir)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )