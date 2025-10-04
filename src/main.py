from fastapi import FastAPI, HTTPException, Depends, APIRouter, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import sys
import os
import logging
import traceback
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio
import sys
import io

# Настройка кодировки для Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from transneft_qa_system import TransneftBenchmarkQA
from config import TransneftConfig, EvaluationCriteria
from benchmark_utils import BenchmarkAnalyzer
from database_models import DatabaseManager, ChatMessage, EvaluationResult, db_manager



print("=== Starting Transneft RAG API ===")

# Глобальные переменные
qa_system = None
system_modules_loaded = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global qa_system, system_modules_loaded
    
    try:
        # Пробуем загрузить систему
        qa_system = TransneftBenchmarkQA()
        qa_system.initialize_system()
        system_modules_loaded = True
        logger.info("System loaded successfully")
        
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        logger.info("Running in fallback mode - system will initialize on first request")
        system_modules_loaded = False
    
    yield
    
    # Cleanup
    if qa_system:
        # Добавьте метод cleanup если нужно
        pass
    logger.info("Shutting down...")

# Создаем основное приложение
app = FastAPI(
    title="Transneft RAG System API",
    description="API для вопросно-ответной системы Transneft",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# CORS middleware ДО всех других middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все origins
    allow_credentials=True,
    allow_methods=["*"],   # Разрешаем все методы
    allow_headers=["*"],   # Разрешаем все заголовки
)

# Дополнительный middleware для CORS
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Добавляем CORS headers ко всем ответам
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

# Явная обработка OPTIONS запросов
@app.options("/api/{rest:path}")
async def options_handler():
    return JSONResponse(
        content={"message": "CORS preflight"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        }
    )

# Модели запросов/ответов
class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    result: str
    source_documents: list = []
    confidence: float = 0.0
    status: str = "success"
    message_id: Optional[int] = None

class HealthResponse(BaseModel):
    status: str
    system_ready: bool
    mode: str

class EvaluateRequest(BaseModel):
    sample_size: int = 10

class EvaluateResponse(BaseModel):
    status: str
    results: Dict[str, Any] = {}
    message: str = ""
    evaluation_id: Optional[int] = None

class HistoryResponse(BaseModel):
    session_id: str
    history: List[Dict[str, Any]] = []

class AnalyticsResponse(BaseModel):
    total_questions: int = 0
    average_confidence: float = 0.0
    system_uptime: str = ""
    active_sessions: int = 0
    benchmark_stats: Dict[str, Any] = {}

class AdminStatsResponse(BaseModel):
    system_status: str
    total_requests: int = 0
    error_rate: float = 0.0
    memory_usage: str = ""
    active_connections: int = 0
    database_stats: Dict[str, Any] = {}

class FeedbackRequest(BaseModel):
    message_id: int
    rating: int
    feedback: str = ""

# Создаем роутер с префиксом /api
api_router = APIRouter(prefix="/api", tags=["API"])

# Зависимости
def get_qa_system():
    """Зависимость для получения QA системы"""
    if not system_modules_loaded and not initialize_on_demand():
        raise HTTPException(status_code=503, detail="System is not ready")
    return qa_system

def initialize_on_demand():
    """Инициализация по требованию"""
    global qa_system, system_modules_loaded
    
    if system_modules_loaded and qa_system and hasattr(qa_system, 'rag_system'):
        return True
        
    try:
        print(">>> On-demand initialization...")
        qa_system = TransneftBenchmarkQA()
        success = qa_system.initialize_system()
        system_modules_loaded = True
        print(f">>> On-demand init completed: {success}")
        return True
    except Exception as e:
        print(f">>> On-demand initialization failed: {e}")
        return False

# Временное хранилище для демонстрации (в продакшене использовать БД)
chat_history_storage = {}
analytics_data = {
    "total_questions": 0,
    "total_requests": 0,
    "start_time": datetime.now().isoformat()
}

# Роуты без префикса (для обратной совместимости)
@app.get("/", tags=["Root"])
async def root():
    """Корневой endpoint"""
    return {
        "message": "Transneft RAG System API",
        "system_ready": system_modules_loaded,
        "mode": "normal" if system_modules_loaded else "fallback",
        "docs_url": "/docs",
        "api_base": "/api"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_legacy():
    """Health check endpoint (legacy)"""
    return HealthResponse(
        status="ready" if system_modules_loaded else "initializing",
        system_ready=system_modules_loaded,
        mode="normal" if system_modules_loaded else "fallback"
    )

# === ВСЕ ENDPOINTS ИЗ API КЛИЕНТА ===

@api_router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="ready" if system_modules_loaded else "initializing",
        system_ready=system_modules_loaded,
        mode="normal" if system_modules_loaded else "fallback"
    )

@api_router.post("/initialize")
async def initialize_system():
    """Явная инициализация системы"""
    global analytics_data
    
    if analytics_data["start_time"] is None:
        analytics_data["start_time"] = datetime.now().isoformat()
    
    if initialize_on_demand():
        return {"status": "success", "message": "System initialized successfully"}
    else:
        raise HTTPException(status_code=500, detail="System initialization failed")

@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, qa_system = Depends(get_qa_system)):
    """Основной endpoint для вопросов"""
    try:
        # Обновляем аналитику
        analytics_data["total_questions"] += 1
        analytics_data["total_requests"] += 1
        
        # Получаем ответ от системы
        result = qa_system.ask_question(
            request.question,
            request.session_id,
            "user"
        )
        
        # Сохраняем в историю
        if request.session_id not in chat_history_storage:
            chat_history_storage[request.session_id] = []
        
        chat_history_storage[request.session_id].append({
            "question": request.question,
            "answer": result.get("result", ""),
            "sources": result.get("source_documents", []),
            "timestamp": datetime.now().isoformat(),
            "message_id": result.get("message_id"),
            "confidence": result.get("confidence", 0.0)
        })
        
        # Преобразуем результат в ожидаемый формат
        return ChatResponse(
            result=result.get("result", ""),
            source_documents=result.get("source_documents", []),
            confidence=result.get("confidence", 0.0),
            message_id=result.get("message_id")
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        analytics_data["total_requests"] += 1
        raise HTTPException(
            status_code=500, 
            detail=f"Ошибка обработки запроса: {str(e)}"
        )

@api_router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_chat_history(session_id: str):
    """Получить историю чата по session_id"""
    try:
        # Пробуем получить из базы данных
        db_messages = db_manager.get_chat_history(session_id)
        
        if db_messages:
            history = []
            for msg in db_messages:
                try:
                    sources = json.loads(msg['sources']) if msg['sources'] else []
                except:
                    sources = []
                    
                history.append({
                    "question": msg['question'],
                    "answer": msg['answer'],
                    "sources": sources,
                    "timestamp": msg['timestamp'],
                    "message_id": msg['id'],
                    "response_time": msg.get('response_time', 0.0)
                })
            return HistoryResponse(session_id=session_id, history=history)
        else:
            # Используем временное хранилище
            history = chat_history_storage.get(session_id, [])
            return HistoryResponse(session_id=session_id, history=history)
            
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        history = chat_history_storage.get(session_id, [])
        return HistoryResponse(session_id=session_id, history=history)

@api_router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_system(request: EvaluateRequest, background_tasks: BackgroundTasks, qa_system = Depends(get_qa_system)):
    """Оценка системы"""
    try:
        # Запускаем оценку в фоновом режиме
        async def run_evaluation():
            try:
                evaluation_results = qa_system.evaluate_system(request.sample_size)
                return evaluation_results
            except Exception as e:
                logger.error(f"Evaluation error: {e}")
                return None
        
        # Запускаем асинхронно
        evaluation_results = await run_evaluation()
        
        if evaluation_results:
            metrics = evaluation_results.get('metrics', {})
            eval_result = evaluation_results.get('evaluation_result')
            
            return EvaluateResponse(
                status="success",
                results=metrics,
                message=f"Evaluation completed for {metrics.get('num_evaluated', 0)} samples",
                evaluation_id=eval_result.evaluation_id if hasattr(eval_result, 'evaluation_id') else None
            )
        else:
            raise HTTPException(status_code=500, detail="Evaluation failed")
            
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@api_router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(qa_system = Depends(get_qa_system)):
    """Получить аналитику использования"""
    try:
        # Получаем статистику из базы данных
        db_stats = db_manager.get_chat_statistics()
        
        # Получаем статистику бенчмарка
        analyzer = BenchmarkAnalyzer()
        benchmark_stats = analyzer.get_basic_stats() if analyzer.data else {}
        
        return AnalyticsResponse(
            total_questions=db_stats.get('total_messages', analytics_data["total_questions"]),
            average_confidence=0.75,  # Можно вычислить из реальных данных
            system_uptime=analytics_data.get("start_time", "Unknown"),
            active_sessions=len(chat_history_storage),
            benchmark_stats=benchmark_stats
        )
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return AnalyticsResponse(
            total_questions=analytics_data["total_questions"],
            average_confidence=0.0,
            system_uptime=analytics_data.get("start_time", "Unknown"),
            active_sessions=len(chat_history_storage),
            benchmark_stats={}
        )

@api_router.get("/admin/stats", response_model=AdminStatsResponse)
async def get_admin_stats(qa_system = Depends(get_qa_system)):
    """Статистика для админа"""
    try:
        db_stats = db_manager.get_chat_statistics()
        
        return AdminStatsResponse(
            system_status="operational" if system_modules_loaded else "degraded",
            total_requests=analytics_data["total_requests"],
            error_rate=0.02,  # Можно вычислить из реальных данных
            memory_usage="512MB / 2GB",  # Демо-значение
            active_connections=len(chat_history_storage),
            database_stats={
                "total_messages": db_stats.get('total_messages', 0),
                "rated_messages": db_stats.get('rated_messages', 0),
                "avg_rating": db_stats.get('avg_rating', 0),
                "avg_response_time": db_stats.get('avg_response_time', 0)
            }
        )
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        return AdminStatsResponse(
            system_status="degraded",
            total_requests=analytics_data["total_requests"],
            error_rate=0.0,
            memory_usage="Unknown",
            active_connections=0,
            database_stats={}
        )

@api_router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Добавление отзыва к сообщению"""
    try:
        success = db_manager.add_feedback(request.message_id, request.rating, request.feedback)
        
        if success:
            return {"status": "success", "message": "Feedback submitted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to submit feedback")
            
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

# === ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS ===

@api_router.get("/system/status")
async def system_status(qa_system = Depends(get_qa_system)):
    """Детальный статус системы"""
    try:
        db_stats = db_manager.get_chat_statistics()
        
        return {
            "system_ready": system_modules_loaded,
            "mode": "normal" if system_modules_loaded else "fallback",
            "qa_system_available": qa_system is not None,
            "chat_sessions_count": len(chat_history_storage),
            "database_stats": db_stats
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {
            "system_ready": system_modules_loaded,
            "mode": "normal" if system_modules_loaded else "fallback",
            "qa_system_available": qa_system is not None,
            "chat_sessions_count": len(chat_history_storage),
            "database_stats": {}
        }

@api_router.post("/system/reload")
async def reload_system():
    """Принудительная перезагрузка системы"""
    global qa_system, system_modules_loaded
    
    try:
        if initialize_on_demand():
            return {"status": "success", "message": "System reloaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reload system")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}")

@api_router.get("/benchmark/stats")
async def get_benchmark_stats(qa_system = Depends(get_qa_system)):
    """Статистика бенчмарка"""
    try:
        analyzer = BenchmarkAnalyzer()
        
        if analyzer.data:
            stats = analyzer.get_basic_stats()
            return {
                "status": "success",
                "benchmark_stats": stats
            }
        else:
            return {
                "status": "error",
                "message": "Benchmark not loaded",
                "benchmark_stats": {}
            }
    except Exception as e:
        logger.error(f"Error getting benchmark stats: {e}")
        return {
            "status": "error",
            "message": str(e),
            "benchmark_stats": {}
        }

# Подключаем роутер к приложению
app.include_router(api_router)

# Обработчики ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="127.0.0.1",  # Явно указываем localhost
        port=8001,
        log_level="info",
    )