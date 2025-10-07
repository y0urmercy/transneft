import os
import sys
import time
from typing import Dict, List, Tuple

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

    def answer_question(self, question: str) -> str:
        """Основной метод для ответа на вопросы пользователей"""
        if not self.initialized:
            return "Система не инициализирована. Запустите настройку системы."

        if not question or not question.strip():
            return "Пожалуйста, задайте вопрос о ПАО «Транснефть»."

        start_time = time.time()

        try:
            # 1. Поиск релевантных контекстов
            search_results = self.vector_store.search(
                question,
                k=TOP_K_RESULTS,
                threshold=SIMILARITY_THRESHOLD
            )

            if not search_results:
                return "К сожалению, в базе знаний ПАО «Транснефть» нет информации по вашему вопросу. Попробуйте переформулировать вопрос."

            # 2. Извлечение контекстов
            contexts = [chunk for chunk, metadata, score in search_results]

            # 3. Генерация ответа
            answer = self.retrieval_engine.answer_question(question, contexts)

            processing_time = time.time() - start_time
            print(f"⏱️  Время обработки: {processing_time:.2f} сек")

            return answer

        except Exception as e:
            print(f"❌ Ошибка при обработке вопроса: {e}")
            return "Произошла ошибка при обработке вашего вопроса. Пожалуйста, попробуйте еще раз."

    def get_search_stats(self, question: str) -> Dict:
        """Возвращает статистику поиска для отладки"""
        if not self.initialized:
            return {"error": "Система не инициализирована"}

        try:
            search_results = self.vector_store.search(question, k=TOP_K_RESULTS)

            return {
                'question': question,
                'question_type': self.retrieval_engine.analyze_question_type(question),
                'results_found': len(search_results),
                'top_scores': [score for _, _, score in search_results],
                'top_sections': [metadata.get('sections', ['Unknown'])[0] for _, metadata, _ in search_results]
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
            answer = qa_system.answer_question(question)
            print(f"   💡 Ответ: {answer}")

            stats = qa_system.get_search_stats(question)
            print(f"   📊 Статистика: {stats['results_found']} результатов, лучший score: {stats['top_scores'][0]:.3f}")

        print("\n✅ Тестирование завершено успешно!")

    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")