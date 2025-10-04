"""
Конфигурационный файл системы Транснефть QA
Настройки модели, путей и параметров системы
"""

import os
from typing import Dict, Any, List

class TransneftConfig:
    """Основной класс конфигурации для системы Транснефть"""
    
    # ==================== ПУТИ К ДАННЫМ ====================
    BENCHMARK_PATH = "src/data_processing/data/processed/qa_benchmark_final.json"
    VECTOR_STORE_PATH = "vector_stores/transneft_faiss"
    RESULTS_PATH = "results"
    MODEL_CACHE_DIR = "models"
    
    # ==================== МОДЕЛИ ЭМБЕДДИНГОВ ====================
    EMBEDDING_MODELS = {
        "default": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "large": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "russian_optimized": "sentence-transformers/distiluse-base-multilingual-cased-v2"
    }
    
    # ==================== НАСТРОЙКИ ОБРАБОТКИ ТЕКСТА ====================
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MIN_CHUNK_LENGTH = 50
    MAX_CHUNK_LENGTH = 2000
    
    # ==================== НАСТРОЙКИ ПОИСКА ====================
    DEFAULT_SEARCH_K = 5
    SEARCH_CONFIGS = {
        "precision": {
            "search_type": "mmr", 
            "k": 3, 
            "fetch_k": 10,
            "lambda_mult": 0.8
        },
        "recall": {
            "search_type": "similarity", 
            "k": 7, 
            "score_threshold": 0.7
        },
        "balanced": {
            "search_type": "mmr", 
            "k": 5, 
            "fetch_k": 15, 
            "lambda_mult": 0.6
        }
    }
    
    # ==================== ПРОМТ-ШАБЛОНЫ ====================
    PROMPT_TEMPLATES = {
        "expert": """
Ты - экспертный ассистент по вопросам ПАО "Транснефть". 
Отвечай ТОЧНО на основе предоставленного контекста.

КОНТЕКСТ:
{context}

ВОПРОС: {question}

ТРЕБОВАНИЯ К ОТВЕТУ:
1. Отвечай ТОЛЬКО на основе контекста
2. Будь точен в цифрах, датах, названиях
3. Сохраняй профессиональный деловой стиль
4. Если информации нет - сообщи об этом явно
5. Для финансовых данных будь особенно внимателен

ОТВЕТ:""",
        
        "detailed": """
Ты - специалист по корпоративной информации ПАО "Транснефть".
Дай развернутый ответ на вопрос, используя только предоставленные данные.

ДАННЫЕ:
{context}

ЗАПРОС: {question}

СФОРМИРУЙ ОТВЕТ, КОТОРЫЙ:
- Точно соответствует контексту
- Содержит все ключевые факты
- Структурирован и понятен
- Не содержит вымышленной информации

ПРОФЕССИОНАЛЬНЫЙ ОТВЕТ:""",
        
        "concise": """
Контекст: {context}

Вопрос: {question}

Краткий ответ на основе контекста:"""
    }
    
    # ==================== НАСТРОЙКИ МОДЕЛЕЙ ====================
    MODEL_CONFIGS = {
        "openai": {
            "model_name": "gpt-3.5-turbo",
            "temperature": 0.1,
            "max_tokens": 1000,
            "timeout": 30
        },
        "local": {
            "model_name": "local/fallback",
            "temperature": 0.1,
            "max_tokens": 500
        }
    }
    
    # ==================== МЕТРИКИ ОЦЕНКИ ====================
    METRICS_CONFIG = {
        "rouge_types": ['rouge1', 'rouge2', 'rougeL'],
        "bleu_weights": [(1.0,), (0.5, 0.5), (0.33, 0.33, 0.34)],
        "bertscore_lang": "ru",
        "evaluation_sample_sizes": [10, 30, 50, 100],
        "score_thresholds": {
            "excellent": 0.8,
            "good": 0.6,
            "acceptable": 0.4,
            "poor": 0.2
        }
    }
    
    # ==================== НАСТРОЙКИ ИНТЕРФЕЙСА ====================
    UI_CONFIG = {
        "page_title": "🤖 Транснефть QA Система",
        "page_icon": "🛢️",
        "layout": "wide",
        "initial_sidebar_state": "expanded",
        "max_chat_history": 50,
        "default_theme": "light"
    }


def get_model_config(mode: str = "balanced") -> Dict[str, Any]:
    """
    Получить конфигурацию модели по режиму работы
    
    Args:
        mode: Режим работы ("precision", "recall", "balanced")
    
    Returns:
        Dict с настройками поиска
    """
    return TransneftConfig.SEARCH_CONFIGS.get(
        mode, 
        TransneftConfig.SEARCH_CONFIGS["balanced"]
    )


def validate_benchmark_path() -> bool:
    """
    Проверить наличие файла бенчмарка
    
    Returns:
        bool: True если файл существует
    """
    return os.path.exists(TransneftConfig.BENCHMARK_PATH)


def get_embedding_model_config(model_size: str = "default") -> Dict[str, Any]:
    """
    Получить конфигурацию модели эмбеддингов
    
    Args:
        model_size: Размер модели ("default", "large", "russian_optimized")
    
    Returns:
        Dict с настройками модели
    """
    model_name = TransneftConfig.EMBEDDING_MODELS.get(
        model_size, 
        TransneftConfig.EMBEDDING_MODELS["default"]
    )
    
    return {
        "model_name": model_name,
        "model_kwargs": {'device': 'cpu'},
        "encode_kwargs": {'normalize_embeddings': True}
    }


def get_prompt_template(template_type: str = "expert") -> str:
    """
    Получить шаблон промта по типу
    
    Args:
        template_type: Тип промта ("expert", "detailed", "concise")
    
    Returns:
        str: Текст шаблона
    """
    return TransneftConfig.PROMPT_TEMPLATES.get(
        template_type,
        TransneftConfig.PROMPT_TEMPLATES["expert"]
    )


def setup_directories() -> None:
    """
    Создать необходимые директории проекта
    """
    directories = [
        TransneftConfig.RESULTS_PATH,
        TransneftConfig.VECTOR_STORE_PATH,
        TransneftConfig.MODEL_CACHE_DIR,
        "data",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


class EvaluationCriteria:
    """Критерии оценки качества системы"""
    
    @staticmethod
    def get_quality_level(score: float, metric: str) -> str:
        """
        Определить уровень качества по метрике
        
        Args:
            score: Значение метрики
            metric: Название метрики
        
        Returns:
            str: Уровень качества
        """
        thresholds = TransneftConfig.METRICS_CONFIG["score_thresholds"]
        
        if score >= thresholds["excellent"]:
            return "Отлично"
        elif score >= thresholds["good"]:
            return "Хорошо"
        elif score >= thresholds["acceptable"]:
            return "Удовлетворительно"
        else:
            return "Требует улучшения"
    
    @staticmethod
    def calculate_overall_score(metrics: Dict[str, float]) -> float:
        """
        Рассчитать общий балл системы
        
        Args:
            metrics: Словарь с метриками
        
        Returns:
            float: Общий балл (0-1)
        """
        # Веса метрик
        weights = {
            'rouge1': 0.25,
            'rouge2': 0.20,
            'rougeL': 0.20,
            'bleu': 0.15,
            'bertscore': 0.20
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in metrics:
                total_score += metrics[metric] * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    

# ==================== НАСТРОЙКИ БАЗЫ ДАННЫХ ====================
DATABASE_CONFIG = {
    "db_path": "data/chat_history.db",
    "backup_enabled": True,
    "backup_interval_hours": 24,
    "max_history_days": 365,
    "export_formats": ["json", "csv"]
}

# ==================== НАСТРОЙКИ СЕССИЙ ====================
SESSION_CONFIG = {
    "session_timeout_minutes": 120,
    "max_messages_per_session": 1000,
    "enable_session_analytics": True
}