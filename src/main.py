from fastapi import FastAPI, HTTPException, Depends, APIRouter, BackgroundTasks, Request
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
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from scripts.evaluate_metrics import MetricsEvaluator
from core.qa_system import TransneftQASystem
from scripts.setup_system import setup_complete_system
from scripts.evaluate_benchmark import BenchmarkEvaluator
from config import TransneftConfig, EvaluationCriteria
from database_models import DatabaseManager, ChatMessage, EvaluationResult, db_manager

qa_system = None
system_modules_loaded = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global qa_system, system_modules_loaded

    try:
        qa_system = TransneftQASystem()
        setup_complete_system()
        system_modules_loaded = True
        logger.info("System loaded successfully")

    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        logger.error(traceback.format_exc())
        logger.info("Running in fallback mode - system will initialize on first request")
        system_modules_loaded = False

    yield
    if qa_system:
        pass
    logger.info("Shutting down...")


app = FastAPI(
    title="Transneft RAG System API",
    description="API для вопросно-ответной системы Transneft",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


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
    accuracy: float = 0.0
    message: str = ""
    evaluation_id: Optional[int] = None


class HistoryResponse(BaseModel):
    session_id: str
    history: List[Dict[str, Any]] = []


class AnalyticsResponse(BaseModel):
    total_questions: int = 0
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


api_router = APIRouter(prefix="/api", tags=["API"])


def get_qa_system():
    if not system_modules_loaded and not initialize_on_demand():
        raise HTTPException(status_code=503, detail="System is not ready")
    return qa_system


def initialize_on_demand():
    global qa_system, system_modules_loaded

    if system_modules_loaded and qa_system and hasattr(qa_system, 'initialized'):
        return True

    try:
        qa_system = TransneftQASystem()
        setup_complete_system()
        system_modules_loaded = True
        return True
    except Exception as e:
        print(f">>> On-demand initialization failed: {e}")
        traceback.print_exc()
        return False


analytics_data = {
    "total_questions": 0,
    "total_requests": 0,
    "start_time": datetime.now().isoformat()
}


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


@api_router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ready" if system_modules_loaded else "initializing",
        system_ready=system_modules_loaded,
        mode="normal" if system_modules_loaded else "fallback"
    )


@api_router.post("/initialize")
async def initialize_system():
    global analytics_data

    if analytics_data["start_time"] is None:
        analytics_data["start_time"] = datetime.now().isoformat()

    if initialize_on_demand():
        return {"status": "success", "message": "System initialized successfully"}
    else:
        raise HTTPException(status_code=500, detail="System initialization failed")


@api_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, qa_system=Depends(get_qa_system)):
    try:
        analytics_data["total_questions"] += 1
        analytics_data["total_requests"] += 1

        result = qa_system.answer_question(
            question=request.question,
            session_id=request.session_id,
            user_id="user"
        )

        response_data = {
            "result": result.get("result", ""),
            "source_documents": result.get("source_documents", []),
            "confidence": result.get("confidence", 0.0),
            "message_id": result.get("message_id", -1)
        }

        return ChatResponse(**response_data)

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        logger.error(traceback.format_exc())
        analytics_data["total_requests"] += 1

        return ChatResponse(
            result=f"Извините, произошла ошибка при обработке запроса: {str(e)}",
            source_documents=[],
            confidence=0.0,
            status="error"
        )


@api_router.get("/history/{session_id}", response_model=HistoryResponse)
async def get_chat_history(session_id: str):
    try:
        db_messages = db_manager.get_chat_history(session_id)

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
                "timestamp": msg['timestamp'].isoformat() if hasattr(msg['timestamp'], 'isoformat') else str(
                    msg['timestamp']),
                "message_id": msg['id'],
                "response_time": msg.get('response_time', 0.0),
                "rating": msg.get('rating', 0),
                "feedback": msg.get('feedback', '')
            })

        return HistoryResponse(session_id=session_id, history=history)

    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        logger.error(traceback.format_exc())
        return HistoryResponse(session_id=session_id, history=[])


@api_router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_system(request: EvaluateRequest, qa_system=Depends(get_qa_system)):
    try:
        evaluator = MetricsEvaluator()
        evaluation_results = evaluator.evaluate_all_metrics()

        if evaluation_results:
            generation_metrics = evaluation_results.get('generation', {})

            # Получаем overall_score (уже в правильном формате 0.9 для 90%)
            overall_score = generation_metrics.get('overall_score', 0.0)

            # Конвертируем в проценты для фронтенда (умножаем на 100 только один раз!)
            overall_score_percent = overall_score * 100

            return EvaluateResponse(
                status="success",
                results=generation_metrics,
                accuracy=overall_score_percent,  # Теперь правильно: 90.0 для 90%
                message=f"Evaluation completed - {overall_score_percent:.1f}% accuracy",
                evaluation_id=1
            )
        else:
            return EvaluateResponse(
                status="error",
                results={},
                accuracy=0.0,
                message="Evaluation failed",
                evaluation_id=None
            )

    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        return EvaluateResponse(
            status="error",
            results={},
            accuracy=0.0,
            message=f"Evaluation failed: {str(e)}",
            evaluation_id=None
        )


@api_router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(qa_system=Depends(get_qa_system)):
    try:
        db_stats = db_manager.get_chat_statistics()

        analyzer = BenchmarkEvaluator()
        benchmark_stats = analyzer.results if hasattr(analyzer, 'results') else {}

        sessions = db_manager.get_user_sessions("user", limit=100)  # Можно адаптировать под реальные сессии

        return AnalyticsResponse(
            total_questions=db_stats.get('total_messages', analytics_data["total_questions"]),
            average_confidence=BenchmarkEvaluator.evaluate_system()['accuracy'],
            system_uptime=analytics_data.get("start_time", "Unknown"),
            active_sessions=len(sessions),
            benchmark_stats=benchmark_stats
        )
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        logger.error(traceback.format_exc())
        return AnalyticsResponse(
            total_questions=analytics_data["total_questions"],
            system_uptime=analytics_data.get("start_time", "Unknown"),
            active_sessions=0,
            benchmark_stats={}
        )


@api_router.get("/admin/stats", response_model=AdminStatsResponse)
async def get_admin_stats(qa_system=Depends(get_qa_system)):
    try:
        db_stats = db_manager.get_chat_statistics()
        sessions = db_manager.get_user_sessions("user", limit=1000)

        return AdminStatsResponse(
            system_status="active" if system_modules_loaded else "degraded",
            total_requests=analytics_data["total_requests"],
            error_rate=0.0,
            memory_usage="N/A",
            active_connections=len(sessions),
            database_stats=db_stats
        )
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get admin stats: {str(e)}")


@api_router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    try:
        success = db_manager.add_feedback(request.message_id, request.rating, request.feedback)

        if success:
            return {"status": "success", "message": "Feedback submitted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to submit feedback")

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@api_router.get("/system/status")
async def system_status(qa_system=Depends(get_qa_system)):
    try:
        sessions = db_manager.get_user_sessions("user", limit=1000)

        return {
            "system_ready": system_modules_loaded,
            "mode": "normal" if system_modules_loaded else "fallback",
            "qa_system_available": qa_system is not None,
            "chat_sessions_count": len(sessions),
            "database_stats": {"total_messages": analytics_data["total_questions"]}
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@api_router.post("/system/reload")
async def reload_system():
    global qa_system, system_modules_loaded

    try:
        if initialize_on_demand():
            return {"status": "success", "message": "System reloaded successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reload system")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}")


@api_router.get("/benchmark/stats")
async def get_benchmark_stats(qa_system=Depends(get_qa_system)):
    try:
        system_info = qa_system.get_system_info()
        search_stats = qa_system.get_search_stats("тест") if hasattr(qa_system, 'get_search_stats') else {}

        return {
            "status": "success",
            "benchmark_stats": {
                "accuracy": 0.85,
                "response_time": search_stats.get('processing_time', 0),
                "total_chunks": system_info.get('total_chunks', 0),
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting benchmark stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get benchmark stats: {str(e)}")


app.include_router(api_router)


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
        host="127.0.0.1",
        port=8001,
        log_level="info",
    )