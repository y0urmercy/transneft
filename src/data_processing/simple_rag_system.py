# scripts/simple_rag_system.py
import json
from vector_store import VectorStore
from typing import List, Dict


class SimpleRAGSystem:
    """Упрощенная RAG система без зависимостей от тяжелых моделей"""

    def __init__(self, vector_store_path: str = "models/vector_store"):
        print("Инициализация упрощенной RAG системы...")

        # Загружаем векторное хранилище
        self.vector_store = VectorStore()
        self.vector_store.load_index(vector_store_path)

        print("✅ Упрощенная RAG система готова")

    def answer_question(self, question: str, k_retrieval: int = 3) -> Dict:
        """Генерирует ответ на вопрос используя семантический поиск"""

        # Шаг 1: Поиск релевантных chunks
        retrieved_docs = self.vector_store.search(question, k=k_retrieval)

        if not retrieved_docs:
            return {
                "answer": "Не найдено релевантной информации в базе знаний.",
                "sources": [],
                "confidence": 0.0
            }

        # Шаг 2: Извлекаем наиболее релевантную информацию
        answer = self._extract_best_answer(question, retrieved_docs)

        # Шаг 3: Формируем результат
        sources = []
        total_confidence = 0.0

        for doc_text, metadata, score in retrieved_docs:
            sources.append({
                "content": doc_text[:200] + "...",
                "sections": metadata.get('sections', []),
                "score": score,
                "chunk_id": metadata.get('chunk_id')
            })
            total_confidence += score

        avg_confidence = total_confidence / len(retrieved_docs) if retrieved_docs else 0.0

        return {
            "answer": answer,
            "sources": sources,
            "confidence": avg_confidence,
            "retrieved_docs_count": len(retrieved_docs)
        }

    def _extract_best_answer(self, question: str, retrieved_docs: List) -> str:
        """Извлекает лучший ответ из найденных документов"""
        question_words = set(question.lower().split())

        best_answer = ""
        best_score = 0

        for doc_text, metadata, score in retrieved_docs:
            # Разбиваем документ на предложения
            sentences = [s.strip() for s in doc_text.split('.') if s.strip()]

            for sentence in sentences:
                if len(sentence) < 20:  # Пропускаем слишком короткие предложения
                    continue

                sentence_words = set(sentence.lower().split())
                common_words = question_words.intersection(sentence_words)
                relevance_score = len(common_words)

                if relevance_score > best_score:
                    best_score = relevance_score
                    best_answer = sentence

        if best_answer:
            return f"На основе предоставленной информации: {best_answer.strip()}."
        else:
            # Возвращаем начало наиболее релевантного документа
            most_relevant_doc = retrieved_docs[0][0]
            return f"Наиболее релевантная информация: {most_relevant_doc[:300]}..."


# Тестируем упрощенную систему
if __name__ == "__main__":
    rag_system = SimpleRAGSystem()

    test_questions = [
        "Когда была основана компания Транснефть?",
        "Какой уставный капитал у Транснефти?",
        "Сколько километров трубопроводов у компании?"
    ]

    print("🧪 ТЕСТИРОВАНИЕ УПРОЩЕННОЙ RAG СИСТЕМЫ:")
    for question in test_questions:
        result = rag_system.answer_question(question)
        print(f"\n❓ {question}")
        print(f"💬 {result['answer']}")
        print(f"📊 Уверенность: {result['confidence']:.3f}")