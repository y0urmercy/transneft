# scripts/quick_metrics.py
import json
import numpy as np
from simple_rag_system import SimpleRAGSystem


def calculate_basic_metrics():
    """Быстрый расчет базовых метрик"""

    rag_system = SimpleRAGSystem()

    # Загружаем QA бенчмарк
    with open("data/processed/qa_benchmark_final.json", "r", encoding="utf-8") as f:
        qa_benchmark = json.load(f)

    results = []

    for i, qa_pair in enumerate(qa_benchmark[:20]):  # Только 20 для скорости
        question = qa_pair['question']
        expected_chunk = qa_pair['chunk_id']

        result = rag_system.answer_question(question)

        # Проверяем, найден ли правильный chunk
        correct_chunk_found = any(
            source.get('chunk_id') == expected_chunk
            for source in result['sources']
        )

        results.append({
            'question': question,
            'confidence': result['confidence'],
            'correct_chunk_found': correct_chunk_found,
            'sources_count': len(result['sources'])
        })

    # Базовые метрики
    avg_confidence = np.mean([r['confidence'] for r in results])
    accuracy = np.mean([r['correct_chunk_found'] for r in results])

    metrics = {
        "retrieval_accuracy": accuracy,
        "average_confidence": avg_confidence,
        "evaluated_questions": len(results)
    }

    print("📊 БАЗОВЫЕ МЕТРИКИ СИСТЕМЫ:")
    print(f"Точность ретривера: {accuracy:.3f}")
    print(f"Средняя уверенность: {avg_confidence:.3f}")
    print(f"Оценено вопросов: {len(results)}")

    # Сохраняем
    with open("data/processed/basic_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == "__main__":
    calculate_basic_metrics()