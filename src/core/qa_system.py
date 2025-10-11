import os
import warnings
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any
from datetime import datetime
import uuid
import time
import sys

from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu
import evaluate
from bert_score import score as bert_score

from config import TransneftConfig, EvaluationCriteria 
from benchmark_utils import BenchmarkAnalyzer, export_benchmark_report
from database_models import DatabaseManager, ChatMessage, EvaluationResult, db_manager
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction  

# Добавляем путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, src_root)

from utils.config import VECTOR_STORE_DIR, TOP_K_RESULTS, SIMILARITY_THRESHOLD
from core.vector_store import VectorStore
from core.retrieval_engine import RetrievalEngine


class TransneftQASystem:
    """Полноценная QA система для ПАО «Транснефть»"""

    def __init__(self, vector_store_path: str = VECTOR_STORE_DIR):
        print("🚀 Инициализация QA системы ПАО «Транснефть»...")
        self.vector_store = VectorStore()
        self.retrieval_engine = RetrievalEngine()
        self.vector_store_path = vector_store_path
        self.initialized = False
        self.processing_time = None
        self.db_manager = db_manager  # Используем глобальный db_manager

        try:
            self.vector_store.load_index(vector_store_path)
            self.initialized = True
            print("✅ QA система успешно инициализирована и готова к работе!")

            # Показываем статистику
            stats = self.vector_store.get_stats()
            print(f"📊 Статистика системы: {stats['total_chunks']} chunks, {stats['total_vectors']} векторов")

        except Exception as e:
            print(f"❌ Ошибка инициализации QA системы: {e}")
            print("\n💡 Решение: Запустите настройку системы:")
            print("   python scripts/setup_system.py")
            raise

    def answer_question(self, question: str, session_id: str = "default", user_id: str = "user") -> Dict[str, Any]:
        """Основной метод для ответа на вопросы пользователей"""
        if not self.initialized:
            return {
                "result": "Система не инициализирована. Запустите настройку системы.",
                "source_documents": [],
                "confidence": 0.0
            }

        if not question or not question.strip():
            return {
                "result": "Пожалуйста, задайте вопрос о ПАО «Транснефть».",
                "source_documents": [],
                "confidence": 0.0
            }

        start_time = time.time()

        try:
            # 1. Поиск релевантных контекстов
            search_results = self.vector_store.search(
                question,
                k=TOP_K_RESULTS,
                threshold=SIMILARITY_THRESHOLD
            )

            if not search_results:
                return {
                    "result": "К сожалению, в базе знаний ПАО «Транснефть» нет информации по вашему вопросу. Попробуйте переформулировать вопрос.",
                    "source_documents": [],
                    "confidence": 0.0
                }

            # 2. Извлечение контекстов
            contexts = [chunk for chunk, metadata, score in search_results]
            source_documents = [
                {
                    "content": chunk,
                    "metadata": metadata,
                    "score": float(score)
                }
                for chunk, metadata, score in search_results
            ]

            # 3. Генерация ответа
            answer = self.retrieval_engine.answer_question(question, contexts)

            self.processing_time = time.time() - start_time
            
            # Сохраняем в базу данных
            message_id = -1
            try:
                chat_message = ChatMessage(
                    session_id=session_id,
                    user_id=user_id,
                    question=question,
                    answer=answer,
                    sources=json.dumps(source_documents, ensure_ascii=False),
                    timestamp=datetime.now(),
                    response_time=self.processing_time,
                    model_used="transneft_qa_system"
                )
                message_id = self.db_manager.save_chat_message(chat_message)
            except Exception as db_error:
                print(f"⚠️ Ошибка сохранения в БД: {db_error}")

            return {
                "result": answer,
                "source_documents": source_documents,
                "confidence": float(search_results[0][2]) if search_results else 0.8,
                "message_id": message_id,
                "processing_time": self.processing_time
            }

        except Exception as e:
            print(f"❌ Ошибка при обработке вопроса: {e}")
            return {
                "result": f"Произошла ошибка при обработке вашего вопроса: {str(e)}",
                "source_documents": [],
                "confidence": 0.0,
                "error": str(e)
            }

    def get_search_stats(self, question: str) -> Dict:
        """Возвращает статистику поиска для отладки"""
        if not self.initialized:
            return {"error": "Система не инициализирована"}

        try:
            search_results = self.vector_store.search(question, k=TOP_K_RESULTS)

            return {
                'question': question,
                'question_type': self.retrieval_engine.analyze_question_type(question) if hasattr(self.retrieval_engine, 'analyze_question_type') else "unknown",
                'results_found': len(search_results),
                'top_scores': [float(score) for _, _, score in search_results],
                'top_sections': [metadata.get('sections', ['Unknown'])[0] if metadata.get('sections') else 'Unknown' for _, metadata, _ in search_results],
                'processing_time': self.processing_time,
            }
        except Exception as e:
            return {"error": str(e)}

    def get_system_info(self) -> Dict:
        """Возвращает информацию о системе"""
        if not self.initialized:
            return {"status": "Не инициализирована"}

        stats = self.vector_store.get_stats()

        return {
            "status": "Активна",
            "vector_store": stats,
            "retrieval_engine": "Retrieval-only (без LLM)",
            "model": stats.get("model", "Unknown"),
            "total_chunks": stats.get("total_chunks", 0),
            "similarity_threshold": SIMILARITY_THRESHOLD
        }
        
    def load_chat_history(self, session_id: str) -> List[Tuple[str, str, list, str]]:
        """Загрузка истории чата из БД"""
        try:
            messages = self.db_manager.get_chat_history(session_id)
            chat_history = []
            for msg in messages:
                try:
                    sources = json.loads(msg['sources']) if msg['sources'] else []
                except:
                    sources = []

                try:
                    timestamp_str = msg['timestamp'].strftime("%H:%M:%S") if hasattr(msg['timestamp'], 'strftime') else str(msg['timestamp'])
                except:
                    timestamp_str = ""

                chat_history.append((
                    msg['question'] if msg['question'] else "",
                    msg['answer'] if msg['answer'] else "",
                    sources,
                    timestamp_str
                ))
            return chat_history
        except Exception as e:
            print(f"❌ Ошибка загрузки истории: {e}")
            return []

    def test_connection(self) -> bool:
        """Проверяет работоспособность системы"""
        if not self.initialized:
            return False

        try:
            # Простой тестовый запрос
            test_results = self.vector_store.search("Транснефть", k=1)
            return len(test_results) > 0
        except:
            return False


if __name__ == "__main__":
    # Тестирование QA системы
    try:
        qa_system = TransneftQASystem()

        test_questions = [
            "Сколько акций в уставном капитале?",
            "Когда была зарегистрирована компания?",
            "Какие основные направления деятельности?",
            "Кто является аудитором компании?"
        ]

        print("\n🧪 ТЕСТИРОВАНИЕ QA СИСТЕМЫ:")
        print("=" * 50)

        for i, question in enumerate(test_questions, 1):
            print(f"\n{i}. ❓ Вопрос: {question}")
            result = qa_system.answer_question(question, "test_session")
            print(f"   💡 Ответ: {result['result']}")
            print(f"   📊 Уверенность: {result['confidence']:.3f}")
            print(f"   📄 Источники: {len(result['source_documents'])}")

        print("\n✅ Тестирование завершено успешно!")

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")