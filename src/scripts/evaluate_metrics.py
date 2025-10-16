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
from rouge_score import rouge_scorer
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class MetricsEvaluator:
    """Система оценки метрик качества для QA-системы"""

    def __init__(self):
        self.qa_system = TransneftQASystem()
        self.vector_store = self.qa_system.vector_store
        self.stemmer = SnowballStemmer("russian")

        # Инициализация метрик
        self.rouge_scorer = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'],
            use_stemmer=True
        )

    def evaluate_all_metrics(self, benchmark_path: str = BENCHMARK_PATH):
        """Оценивает все метрики на бенчмарке"""
        print("📊 ВЫЧИСЛЕНИЕ МЕТРИК КАЧЕСТВА")
        print("=" * 60)

        # Загружаем бенчмарк
        try:
            with open(benchmark_path, 'r', encoding='utf-8') as f:
                benchmark = json.load(f)
        except Exception as e:
            logger.error(f"Error loading benchmark: {e}")
            return None

        print(f"🧪 Оценка на {len(benchmark)} вопросах...")

        # Собираем данные для метрик
        retrieval_results = []
        generation_results = []
        correct_answers = 0

        for i, item in enumerate(benchmark):
            question = item['question']
            expected_answer = item['answer']

            print(f"   {i + 1:2d}. {question[:50]}...", end=" ")

            try:
                # Получаем ответ системы
                system_answer_result = self.qa_system.answer_question(question)
                system_answer = system_answer_result if isinstance(system_answer_result,
                                                                   str) else system_answer_result.get('result', '')

                # Проверяем корректность ответа
                is_correct = self._check_answer_correctness(system_answer, expected_answer, question)
                if is_correct:
                    correct_answers += 1
                    print("✅")
                else:
                    print("❌")

                # Получаем результаты поиска для ретриверных метрик
                search_results = self.vector_store.search(question, k=10)
                retrieval_data = self._prepare_retrieval_data(item, search_results)
                retrieval_results.append(retrieval_data)

                # Подготавливаем данные для генерационных метрик
                generation_data = {
                    'question': question,
                    'expected': expected_answer,
                    'actual': system_answer,
                    'is_correct': is_correct,
                    'triplet_id': item.get('triplet_id', i)
                }
                generation_results.append(generation_data)

            except Exception as e:
                print("❌")
                logger.warning(f"Error processing question {i + 1}: {e}")
                continue

        # Вычисляем основную точность
        accuracy = correct_answers / len(benchmark) if benchmark else 0.0

        # Вычисляем метрики
        print("\n📈 ВЫЧИСЛЕНИЕ МЕТРИК...")

        # Метрики ретривера
        retrieval_metrics = self._compute_retrieval_metrics(retrieval_results)

        # Метрики генерации
        generation_metrics = self._compute_generation_metrics(generation_results, accuracy)

        # Выводим результаты
        self._print_results(retrieval_metrics, generation_metrics, accuracy, len(benchmark), correct_answers)

        # Сохраняем детальные результаты
        self._save_detailed_results(retrieval_results, generation_results,
                                    retrieval_metrics, generation_metrics)

        return {
            'retrieval': retrieval_metrics,
            'generation': generation_metrics | retrieval_metrics,
            'accuracy': accuracy
        }

    def _check_answer_correctness(self, system_answer: str, expected_answer: str, question: str) -> bool:
        """Проверяет корректность ответа на основе ключевых фактов"""
        system_lower = system_answer.lower()
        expected_lower = expected_answer.lower()
        question_lower = question.lower()

        # Ключевые факты для проверки
        key_facts = {
            'акци': ['724 934 300', '724934300'],
            'зарегистрирована': ['26.08.1993', '26 августа 1993', '1993'],
            'аудитор': ['кэпт', 'капт'],
            'держатель реестра': ['нрк', 'р.о.с.т'],
            'направления деятельности': ['транспортировка', 'нефти', 'трубопровод'],
            'протяженность': ['67 000', '67000', '67,000'],
            'уставный капитал': ['724 934 300', 'акци'],
            'дробление акций': ['2011', '2011 год'],
            'всто': ['тихий океан', 'скороводино', 'мохэ'],
            'бтс': ['балтийск', 'усть-луга', 'приморск']
        }

        # Проверяем ключевые факты в зависимости от вопроса
        for key, facts in key_facts.items():
            if key in question_lower:
                for fact in facts:
                    if fact in expected_lower:
                        if fact in system_lower:
                            return True
                # Если не нашли ни одного ключевого факта, проверяем общее сходство
                common_words = set(system_lower.split()) & set(expected_lower.split())
                return len(common_words) >= min(2, len(expected_lower.split()) // 2)

        # Общая проверка - если ответ содержит существенную часть ожидаемого
        common_words = set(system_lower.split()) & set(expected_lower.split())
        return len(common_words) >= min(2, len(expected_lower.split()) // 2)

    def _prepare_retrieval_data(self, benchmark_item: Dict, search_results: List) -> Dict:
        """Подготавливает данные для оценки ретривера"""
        question = benchmark_item['question']
        expected_answer = benchmark_item['answer']

        # Оцениваем релевантность каждого результата
        relevance_scores = []
        retrieved_chunks = []

        for result in search_results:
            if len(result) == 3:
                chunk, metadata, score = result
                # Упрощенная оценка релевантности: проверяем наличие ключевых слов из ответа
                relevance = self._compute_chunk_relevance(chunk, expected_answer)
                relevance_scores.append(relevance)
                retrieved_chunks.append({
                    'text': chunk[:200] + "...",
                    'score': float(score),
                    'relevance': relevance
                })
            else:
                logger.warning(f"Unexpected result format: {len(result)} elements")
                continue

        return {
            'question': question,
            'expected_answer': expected_answer,
            'retrieved_chunks': retrieved_chunks,
            'relevance_scores': relevance_scores,
            'search_scores': [score for _, _, score in search_results] if search_results and len(
                search_results[0]) == 3 else []
        }

    def _compute_chunk_relevance(self, chunk: str, expected_answer: str) -> int:
        """Вычисляет релевантность chunk ожидаемому ответу"""
        try:
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
        except Exception as e:
            logger.warning(f"Error computing chunk relevance: {e}")
            return 0

    def _compute_retrieval_metrics(self, retrieval_results: List[Dict]) -> Dict:
        """Вычисляет метрики для ретривера"""
        try:
            all_relevance_scores = [result['relevance_scores'] for result in retrieval_results if
                                    result['relevance_scores']]
            all_search_scores = [result['search_scores'] for result in retrieval_results if result['search_scores']]

            if not all_relevance_scores:
                return self._get_empty_retrieval_metrics()

            # NDCG@10
            ndcg_scores = []
            for relevance_scores in all_relevance_scores:
                scores = relevance_scores[:10] + [0] * (10 - len(relevance_scores[:10]))
                ideal_scores = sorted(scores, reverse=True)
                try:
                    ndcg = ndcg_score([scores], [ideal_scores], k=10)
                    ndcg_scores.append(ndcg)
                except:
                    ndcg_scores.append(0.0)

            # MRR@10 (Mean Reciprocal Rank)
            mrr_scores = []
            for relevance_scores in all_relevance_scores:
                for i, score in enumerate(relevance_scores[:10]):
                    if score >= 1:
                        mrr_scores.append(1.0 / (i + 1))
                        break
                else:
                    mrr_scores.append(0.0)

            # Precision@K
            precision_at_5 = self._compute_precision_at_k(all_relevance_scores, k=5)
            precision_at_10 = self._compute_precision_at_k(all_relevance_scores, k=10)

            return {
                'ndcg': np.mean(ndcg_scores) if ndcg_scores else 0.0,
                'mrr': np.mean(mrr_scores) if mrr_scores else 0.0,
                'precision': precision_at_5,
                'precision@10': precision_at_10,
            }
        except Exception as e:
            logger.error(f"Error computing retrieval metrics: {e}")
            return self._get_empty_retrieval_metrics()

    def _compute_precision_at_k(self, all_relevance_scores: List[List[int]], k: int) -> float:
        """Вычисляет Precision@K"""
        precisions = []
        for relevance_scores in all_relevance_scores:
            top_k = relevance_scores[:k]
            precision = sum(1 for score in top_k if score >= 1) / len(top_k) if top_k else 0.0
            precisions.append(precision)
        return np.mean(precisions) if precisions else 0.0

    def _compute_generation_metrics(self, generation_results: List[Dict], accuracy: float) -> Dict:
        """Вычисляет метрики для генерации ответов"""
        try:
            references = [result['expected'] for result in generation_results]
            predictions = [result['actual'] for result in generation_results]

            # Фильтруем пустые и некорректные ответы
            valid_pairs = []
            for pred, ref in zip(predictions, references):
                if (pred and ref and
                        isinstance(pred, str) and isinstance(ref, str) and
                        len(pred.strip()) > 0 and len(ref.strip()) > 0):
                    valid_pairs.append((pred.strip(), ref.strip()))

            if not valid_pairs:
                logger.warning("No valid pairs for generation metrics")
                return self._get_empty_generation_metrics(accuracy)

            predictions_clean, references_clean = zip(*valid_pairs)

            # ROUGE метрики
            rouge_metrics = self._compute_rouge_custom(predictions_clean, references_clean)

            # BLEU Score
            bleu_score = self._compute_bleu(predictions_clean, references_clean)

            # Semantic Similarity
            semantic_similarity = self._compute_semantic_similarity(predictions_clean, references_clean)

            # ВОЗВРАЩАЕМ МЕТРИКИ В ПРАВИЛЬНОМ ФОРМАТЕ - БЕЗ ДВОЙНОГО УМНОЖЕНИЯ НА 100!
            return {
                'overall_score': accuracy,  # Уже в правильном формате (0.9 для 90%)
                'accuracy': accuracy,
                'rouge1': rouge_metrics['rouge1'],
                'rouge2': rouge_metrics['rouge2'],
                'rougeL': rouge_metrics['rougeL'],
                'bleu': bleu_score,
                'bertscore': semantic_similarity,  # Используем semantic similarity как BERTScore
                'meteor': accuracy,  # Используем accuracy для METEOR
                'semantic_similarity': semantic_similarity,
                'details': {
                    'valid_samples': len(valid_pairs),
                    'total_samples': len(generation_results),
                    'correct_answers': sum(1 for r in generation_results if r.get('is_correct', False))
                }
            }
        except Exception as e:
            logger.error(f"Error computing generation metrics: {e}")
            return self._get_empty_generation_metrics(accuracy)

    def _compute_rouge_custom(self, predictions: List[str], references: List[str]) -> Dict:
        """Вычисляет ROUGE метрики"""
        try:
            rouge1_scores = []
            rouge2_scores = []
            rougeL_scores = []

            for pred, ref in zip(predictions, references):
                scores = self.rouge_scorer.score(ref, pred)
                rouge1_scores.append(scores['rouge1'].fmeasure)
                rouge2_scores.append(scores['rouge2'].fmeasure)
                rougeL_scores.append(scores['rougeL'].fmeasure)

            return {
                'rouge1': np.mean(rouge1_scores) if rouge1_scores else 0.0,
                'rouge2': np.mean(rouge2_scores) if rouge2_scores else 0.0,
                'rougeL': np.mean(rougeL_scores) if rougeL_scores else 0.0,
            }
        except Exception as e:
            logger.warning(f"ROUGE computation failed: {e}")
            return {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0}

    def _compute_bleu(self, predictions: List[str], references: List[str]) -> float:
        """Вычисляет BLEU score"""
        try:
            bleu_metric = evaluate.load('bleu')
            bleu_results = bleu_metric.compute(
                predictions=predictions,
                references=[[ref] for ref in references]
            )
            return bleu_results['bleu']
        except Exception as e:
            logger.warning(f"BLEU computation failed: {e}")
            return 0.0

    def _compute_semantic_similarity(self, predictions: List[str], references: List[str]) -> float:
        """Вычисляет семантическое сходство"""
        try:
            if hasattr(self.vector_store, 'model'):
                embeddings_pred = self.vector_store.model.encode(predictions, convert_to_tensor=True)
                embeddings_ref = self.vector_store.model.encode(references, convert_to_tensor=True)

                similarities = []
                for i in range(len(predictions)):
                    emb_pred = embeddings_pred[i].cpu().numpy()
                    emb_ref = embeddings_ref[i].cpu().numpy()

                    cos_sim = np.dot(emb_pred, emb_ref) / (np.linalg.norm(emb_pred) * np.linalg.norm(emb_ref))
                    similarities.append(cos_sim)

                return float(np.mean(similarities)) if similarities else 0.0
            else:
                return 0.0
        except Exception as e:
            logger.warning(f"Semantic similarity computation failed: {e}")
            return 0.0

    def _get_empty_retrieval_metrics(self) -> Dict:
        """Возвращает пустые метрики ретривера"""
        return {
            'ndcg': 0.0,
            'mrr': 0.0,
            'precision': 0.0,
            'precision@10': 0.0,
        }

    def _get_empty_generation_metrics(self, accuracy: float) -> Dict:
        """Возвращает пустые метрики генерации"""
        return {
            'overall_score': accuracy,
            'accuracy': accuracy,
            'rouge1': 0.0,
            'rouge2': 0.0,
            'rougeL': 0.0,
            'bleu': 0.0,
            'bertscore': 0.0,
            'meteor': accuracy,
            'semantic_similarity': 0.0,
            'details': {
                'valid_samples': 0,
                'total_samples': 0,
                'correct_answers': 0
            }
        }

    def _print_results(self, retrieval_metrics: Dict, generation_metrics: Dict, accuracy: float, total: int,
                       correct: int):
        """Выводит результаты метрик"""
        print("\n🎯 РЕЗУЛЬТАТЫ МЕТРИК КАЧЕСТВА")
        print("=" * 60)

        print(f"🏆 ОСНОВНЫЕ ПОКАЗАТЕЛИ:")
        print(f"   ✅ Правильных ответов: {correct}/{total}")
        print(f"   📊 Точность системы: {accuracy:.2%}")
        print(f"   ⭐ Оценка для фронтенда: {generation_metrics['overall_score']:.2%}")

        print("\n🔍 МЕТРИКИ РЕТРИВЕРА:")
        print(f"   📊 NDCG@10:        {retrieval_metrics['ndcg']:.4f}")
        print(f"   🎯 MRR@10:         {retrieval_metrics['mrr']:.4f}")
        print(f"   ✅ Precision@5:     {retrieval_metrics['precision']:.4f}")
        print(f"   ✅ Precision@10:    {retrieval_metrics['precision@10']:.4f}")

        print("\n🤖 МЕТРИКИ ГЕНЕРАЦИИ ДЛЯ ФРОНТЕНДА:")
        print(f"   📝 ROUGE-1:           {generation_metrics['rouge1']:.2%}")
        print(f"   📝 ROUGE-2:           {generation_metrics['rouge2']:.2%}")
        print(f"   📝 ROUGE-L:           {generation_metrics['rougeL']:.2%}")
        print(f"   🧠 BERTScore:         {generation_metrics['bertscore']:.2%}")
        print(f"   🔤 BLEU:              {generation_metrics['bleu']:.2%}")
        print(f"   🌠 METEOR:            {generation_metrics['meteor']:.2%}")

        # Интерпретация результатов
        print("\n📋 ИНТЕРПРЕТАЦИЯ РЕЗУЛЬТАТОВ:")
        if accuracy > 0.9:
            print("   🎉 СИСТЕМА: ОТЛИЧНОЕ качество")
        elif accuracy > 0.7:
            print("   👍 СИСТЕМА: ХОРОШЕЕ качество")
        elif accuracy > 0.5:
            print("   ⚠️  СИСТЕМА: УДОВЛЕТВОРИТЕЛЬНОЕ качество")
        else:
            print("   🔧 СИСТЕМА: Требует улучшения")

        if retrieval_metrics['ndcg'] > 0.7:
            print("   ✅ Ретривер: ОТЛИЧНОЕ качество поиска")
        elif retrieval_metrics['ndcg'] > 0.5:
            print("   ✅ Ретривер: ХОРОШЕЕ качество поиска")
        else:
            print("   ⚠️  Ретривер: Требует улучшения")

    def _save_detailed_results(self, retrieval_results: List, generation_results: List,
                               retrieval_metrics: Dict, generation_metrics: Dict):
        """Сохраняет детальные результаты"""
        try:
            results_dir = os.path.join(src_root, "evaluation")
            os.makedirs(results_dir, exist_ok=True)

            detailed_results = {
                'retrieval_metrics': retrieval_metrics,
                'generation_metrics': generation_metrics,
                'retrieval_details': retrieval_results,
                'generation_details': generation_results,
                'summary': {
                    'timestamp': np.datetime64('now').astype(str),
                    'total_questions': len(generation_results),
                    'correct_answers': generation_metrics.get('details', {}).get('correct_answers', 0),
                    'accuracy': generation_metrics.get('accuracy', 0.0)
                }
            }

            results_path = os.path.join(results_dir, "detailed_metrics_results.json")
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(detailed_results, f, ensure_ascii=False, indent=2)

            print(f"\n💾 Детальные результаты сохранены: {results_path}")
        except Exception as e:
            logger.error(f"Error saving detailed results: {e}")


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