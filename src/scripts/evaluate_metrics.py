import os
import sys
import json
import numpy as np
from typing import List, Dict, Tuple
import evaluate
from sklearn.metrics import ndcg_score
import nltk
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize

# Добавляем путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, src_root)

from core.qa_system import TransneftQASystem
from core.vector_store import VectorStore
from utils.config import BENCHMARK_PATH

# Скачиваем необходимые ресурсы NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


class MetricsEvaluator:
    """Система оценки метрик качества для QA-системы"""

    def __init__(self):
        self.qa_system = TransneftQASystem()
        self.vector_store = self.qa_system.vector_store
        self.stemmer = SnowballStemmer("russian")

        # Загружаем метрики
        self.bleurt = evaluate.load("bleurt", module_type="metric")
        self.rouge = evaluate.load("rouge")

    def evaluate_all_metrics(self, benchmark_path: str = BENCHMARK_PATH):
        """Оценивает все метрики на бенчмарке"""
        print("📊 ВЫЧИСЛЕНИЕ МЕТРИК КАЧЕСТВА")
        print("=" * 60)

        # Загружаем бенчмарк
        with open(benchmark_path, 'r', encoding='utf-8') as f:
            benchmark = json.load(f)

        print(f"🧪 Оценка на {len(benchmark)} вопросах...")

        # Собираем данные для метрик
        retrieval_results = []
        generation_results = []

        for i, item in enumerate(benchmark):
            question = item['question']
            expected_answer = item['answer']

            print(f"   {i + 1:2d}. {question[:50]}...")

            # Получаем ответ системы
            system_answer = self.qa_system.answer_question(question)

            # Получаем результаты поиска для ретриверных метрик
            search_results = self.vector_store.search(question, k=10)
            retrieval_data = self._prepare_retrieval_data(item, search_results)
            retrieval_results.append(retrieval_data)

            # Подготавливаем данные для генерационных метрик
            generation_data = {
                'question': question,
                'expected': expected_answer,
                'actual': system_answer
            }
            generation_results.append(generation_data)

        # Вычисляем метрики
        print("\n📈 ВЫЧИСЛЕНИЕ МЕТРИК...")

        # Метрики ретривера
        retrieval_metrics = self._compute_retrieval_metrics(retrieval_results)

        # Метрики генерации
        generation_metrics = self._compute_generation_metrics(generation_results)

        # Выводим результаты
        self._print_results(retrieval_metrics, generation_metrics)

        # Сохраняем детальные результаты
        self._save_detailed_results(retrieval_results, generation_results,
                                    retrieval_metrics, generation_metrics)

        return {
            'retrieval': retrieval_metrics,
            'generation': generation_metrics
        }

    def _prepare_retrieval_data(self, benchmark_item: Dict, search_results: List) -> Dict:
        """Подготавливает данные для оценки ретривера"""
        question = benchmark_item['question']
        expected_answer = benchmark_item['answer']

        # Оцениваем релевантность каждого результата
        relevance_scores = []
        retrieved_chunks = []

        for chunk, metadata, score in search_results:
            # Упрощенная оценка релевантности: проверяем наличие ключевых слов из ответа
            relevance = self._compute_chunk_relevance(chunk, expected_answer)
            relevance_scores.append(relevance)
            retrieved_chunks.append({
                'text': chunk[:200] + "...",  # Сохраняем превью
                'score': float(score),
                'relevance': relevance
            })

        return {
            'question': question,
            'expected_answer': expected_answer,
            'retrieved_chunks': retrieved_chunks,
            'relevance_scores': relevance_scores,
            'search_scores': [score for _, _, score in search_results]
        }

    def _compute_chunk_relevance(self, chunk: str, expected_answer: str) -> int:
        """Вычисляет релевантность chunk ожидаемому ответу"""
        chunk_lower = chunk.lower()
        expected_lower = expected_answer.lower()

        # Токенизируем и стеммируем
        chunk_words = set(self.stemmer.stem(word) for word in word_tokenize(chunk_lower) if word.isalnum())
        expected_words = set(self.stemmer.stem(word) for word in word_tokenize(expected_lower) if word.isalnum())

        # Вычисляем пересечение
        common_words = chunk_words & expected_words

        if len(common_words) >= min(3, len(expected_words)):
            return 2  # Высокая релевантность
        elif len(common_words) >= 1:
            return 1  # Средняя релевантность
        else:
            return 0  # Низкая релевантность

    def _compute_retrieval_metrics(self, retrieval_results: List[Dict]) -> Dict:
        """Вычисляет метрики для ретривера"""
        all_relevance_scores = [result['relevance_scores'] for result in retrieval_results]
        all_search_scores = [result['search_scores'] for result in retrieval_results]

        # NDCG@10
        ndcg_scores = []
        for relevance_scores in all_relevance_scores:
            # Дополняем до 10 элементов если нужно
            scores = relevance_scores[:10] + [0] * (10 - len(relevance_scores[:10]))
            ideal_scores = sorted(scores, reverse=True)
            ndcg = ndcg_score([scores], [ideal_scores], k=10)
            ndcg_scores.append(ndcg)

        # MRR@10 (Mean Reciprocal Rank)
        mrr_scores = []
        for relevance_scores in all_relevance_scores:
            for i, score in enumerate(relevance_scores[:10]):
                if score >= 1:  # Нашли релевантный документ
                    mrr_scores.append(1.0 / (i + 1))
                    break
            else:
                mrr_scores.append(0.0)

        # MAP@100 (Mean Average Precision)
        map_scores = []
        for relevance_scores in all_relevance_scores:
            precision_scores = []
            relevant_count = 0
            for i, score in enumerate(relevance_scores[:100]):
                if score >= 1:
                    relevant_count += 1
                    precision_scores.append(relevant_count / (i + 1))
            if precision_scores:
                map_scores.append(sum(precision_scores) / len(precision_scores))
            else:
                map_scores.append(0.0)

        return {
            'ndcg@10': np.mean(ndcg_scores),
            'mrr@10': np.mean(mrr_scores),
            'map@100': np.mean(map_scores),
            'details': {
                'ndcg_scores': ndcg_scores,
                'mrr_scores': mrr_scores,
                'map_scores': map_scores
            }
        }

    def _compute_generation_metrics(self, generation_results: List[Dict]) -> Dict:
        """Вычисляет метрики для генерации ответов"""
        references = [result['expected'] for result in generation_results]
        predictions = [result['actual'] for result in generation_results]

        # BLEURT-20
        bleurt_scores = self.bleurt.compute(
            predictions=predictions,
            references=references
        )['scores']

        # ROUGE с стеммингом
        rouge_results = self.rouge.compute(
            predictions=predictions,
            references=references,
            use_stemmer=True
        )

        # Semantic Answer Similarity (упрощенная версия)
        semantic_similarity = self._compute_semantic_similarity(predictions, references)

        return {
            'bleurt': np.mean(bleurt_scores),
            'rouge1': rouge_results['rouge1'],
            'rouge2': rouge_results['rouge2'],
            'rougeL': rouge_results['rougeL'],
            'semantic_similarity': semantic_similarity,
            'details': {
                'bleurt_scores': bleurt_scores,
                'rouge_scores': rouge_results
            }
        }

    def _compute_semantic_similarity(self, predictions: List[str], references: List[str]) -> float:
        """Вычисляет семантическое сходство (упрощенная версия)"""
        # Используем ту же модель, что и для ретривера
        embeddings_pred = self.vector_store.model.encode(predictions, convert_to_tensor=True)
        embeddings_ref = self.vector_store.model.encode(references, convert_to_tensor=True)

        # Вычисляем косинусное сходство
        similarities = []
        for i in range(len(predictions)):
            cos_sim = np.dot(
                embeddings_pred[i].cpu().numpy(),
                embeddings_ref[i].cpu().numpy()
            ) / (np.linalg.norm(embeddings_pred[i].cpu().numpy()) * np.linalg.norm(embeddings_ref[i].cpu().numpy()))
            similarities.append(cos_sim)

        return float(np.mean(similarities))

    def _print_results(self, retrieval_metrics: Dict, generation_metrics: Dict):
        """Выводит результаты метрик"""
        print("\n🎯 РЕЗУЛЬТАТЫ МЕТРИК КАЧЕСТВА")
        print("=" * 60)

        print("🔍 МЕТРИКИ РЕТРИВЕРА:")
        print(f"   📊 NDCG@10:    {retrieval_metrics['ndcg@10']:.4f}")
        print(f"   🎯 MRR@10:     {retrieval_metrics['mrr@10']:.4f}")
        print(f"   🗺️  MAP@100:    {retrieval_metrics['map@100']:.4f}")

        print("\n🤖 МЕТРИКИ ГЕНЕРАЦИИ ОТВЕТОВ:")
        print(f"   💎 BLEURT:            {generation_metrics['bleurt']:.4f}")
        print(f"   📝 ROUGE-1:           {generation_metrics['rouge1']:.4f}")
        print(f"   📝 ROUGE-2:           {generation_metrics['rouge2']:.4f}")
        print(f"   📝 ROUGE-L:           {generation_metrics['rougeL']:.4f}")
        print(f"   🧠 Semantic Similarity: {generation_metrics['semantic_similarity']:.4f}")

        # Интерпретация результатов
        print("\n📋 ИНТЕРПРЕТАЦИЯ РЕЗУЛЬТАТОВ:")
        if retrieval_metrics['ndcg@10'] > 0.7:
            print("   ✅ Ретривер: ОТЛИЧНОЕ качество поиска")
        elif retrieval_metrics['ndcg@10'] > 0.5:
            print("   ✅ Ретривер: ХОРОШЕЕ качество поиска")
        else:
            print("   ⚠️  Ретривер: Требует улучшения")

        if generation_metrics['rougeL'] > 0.7:
            print("   ✅ Генерация: ОТЛИЧНОЕ качество ответов")
        elif generation_metrics['rougeL'] > 0.5:
            print("   ✅ Генерация: ХОРОШЕЕ качество ответов")
        else:
            print("   ⚠️  Генерация: Требует улучшения")

    def _save_detailed_results(self, retrieval_results: List, generation_results: List,
                               retrieval_metrics: Dict, generation_metrics: Dict):
        """Сохраняет детальные результаты"""
        results_dir = os.path.join(src_root, "evaluation")
        os.makedirs(results_dir, exist_ok=True)

        detailed_results = {
            'retrieval_metrics': retrieval_metrics,
            'generation_metrics': generation_metrics,
            'retrieval_details': retrieval_results,
            'generation_details': generation_results,
            'summary': {
                'timestamp': np.datetime64('now').astype(str),
                'total_questions': len(generation_results)
            }
        }

        results_path = os.path.join(results_dir, "detailed_metrics_results.json")
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Детальные результаты сохранены: {results_path}")


def main():
    """Запуск оценки метрик"""
    try:
        evaluator = MetricsEvaluator()
        metrics = evaluator.evaluate_all_metrics()

        print(f"\n🎉 ОЦЕНКА МЕТРИК ЗАВЕРШЕНА!")

    except Exception as e:
        print(f"❌ Ошибка оценки метрик: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()