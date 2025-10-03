from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
import json
from datetime import datetime

# Добавляем путь к исходному коду
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.transneft_qa_system import TransneftBenchmarkQA
from src.database_models import db_manager

app = FastAPI(
    title="Transneft RAG System API",
    description="API для экспертной системы вопросов и ответов ПАО 'Транснефть'",
    version="1.0.0"
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Модели запросов/ответов
class ChatRequest(BaseModel):
    question: str
    session_id: str
    user_id: str = "user"


class ChatResponse(BaseModel):
    result: str
    source_documents: List[Dict]
    message_id: int
    confidence: float


class EvaluationRequest(BaseModel):
    sample_size: int = 30


class InitializeResponse(BaseModel):
    success: bool
    message: str
    system_ready: bool


# Глобальные переменные
qa_system = None
system_ready = False


@app.on_event("startup")
async def startup_event():
    """Инициализация системы при запуске"""
    global qa_system, system_ready
    try:
        qa_system = TransneftBenchmarkQA()
        init_result = qa_system.initialize_system()
        system_ready = init_result > 0
        print("✅ Система инициализирована успешно")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        system_ready = False


@app.get("/")
async def root():
    return {"message": "Transneft RAG System API", "status": "running"}


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy" if system_ready else "initializing",
        "system_ready": system_ready,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/initialize", response_model=InitializeResponse)
async def initialize_system():
    global qa_system, system_ready
    try:
        if qa_system is None:
            qa_system = TransneftBenchmarkQA()

        init_result = qa_system.initialize_system()
        system_ready = init_result > 0

        return InitializeResponse(
            success=system_ready,
            message="Система инициализирована успешно" if system_ready else "Ошибка инициализации",
            system_ready=system_ready
        )
    except Exception as e:
        return InitializeResponse(
            success=False,
            message=f"Ошибка инициализации: {str(e)}",
            system_ready=False
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not system_ready or qa_system is None:
        raise HTTPException(status_code=503, detail="Система не готова")

    try:
        result = qa_system.ask_question(
            request.question,
            request.session_id,
            request.user_id
        )
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки вопроса: {str(e)}")


@app.get("/api/history/{session_id}")
async def get_chat_history(session_id: str):
    if qa_system is None:
        raise HTTPException(status_code=503, detail="Система не инициализирована")

    try:
        history = qa_system.load_chat_history(session_id)
        return {
            "session_id": session_id,
            "messages": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки истории: {str(e)}")


@app.post("/api/evaluate")
async def evaluate_system(request: EvaluationRequest):
    if qa_system is None:
        raise HTTPException(status_code=503, detail="Система не инициализирована")

    try:
        results = qa_system.evaluate_system(request.sample_size)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка оценки системы: {str(e)}")


@app.get("/api/analytics")
async def get_analytics():
    try:
        stats = db_manager.get_chat_statistics("user")
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения аналитики: {str(e)}")


@app.get("/api/admin/stats")
async def get_admin_stats():
    try:
        stats = db_manager.get_chat_statistics()
        eval_history = db_manager.get_evaluation_history(limit=10)

        return {
            "database_stats": stats,
            "evaluation_history": [
                {
                    "evaluation_date": eval_result.evaluation_date.isoformat(),
                    "sample_size": eval_result.sample_size,
                    "overall_score": eval_result.overall_score,
                    "rouge1": eval_result.rouge1,
                    "rouge2": eval_result.rouge2,
                    "bertscore": eval_result.bertscore
                }
                for eval_result in eval_history
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)