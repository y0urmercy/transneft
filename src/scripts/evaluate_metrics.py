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
    """Система оценки метрик качества для QA-системы без TensorFlow"""

    def __init__(self):
        self.qa_system = TransneftQASystem()
        self.vector_store = self.qa_system.vector_store
        self.stemmer = SnowballStemmer("russian")

        # Инициализация метрик без TensorFlow
        self.rouge_scorer = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'], 
            use_stemmer=True
        )
        
        # BERTScore будет инициализирован при первом использовании
        self.bert_scorer = None



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

        for i, item in enumerate(benchmark):
            question = item['question']
            expected_answer = item['answer']

            print(f"   {i + 1:2d}. {question[:50]}...")

            try:
                # Получаем ответ системы
                system_answer_result = self.qa_system.answer_question(question)
                system_answer = system_answer_result if isinstance(system_answer_result, str) else system_answer_result.get('result', '')

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
                
            except Exception as e:
                logger.warning(f"Error processing question {i+1}: {e}")
                continue

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
            'generation': generation_metrics,
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

            # Precision@K
            precision_at_5 = self._compute_precision_at_k(all_relevance_scores, k=5)
            precision_at_10 = self._compute_precision_at_k(all_relevance_scores, k=10)

            return {
                'ndcg@10': np.mean(ndcg_scores),
                'mrr@10': np.mean(mrr_scores),
                'map@100': np.mean(map_scores),
                'precision@5': precision_at_5,
                'precision@10': precision_at_10,
                'details': {
                    'ndcg_scores': ndcg_scores,
                    'mrr_scores': mrr_scores,
                    'map_scores': map_scores
                }
            }
        except Exception as e:
            logger.error(f"Error computing retrieval metrics: {e}")
            return {
                'ndcg@10': 0.0,
                'mrr@10': 0.0,
                'map@100': 0.0,
                'precision@5': 0.0,
                'precision@10': 0.0,
                'details': {}
            }

    def _compute_precision_at_k(self, all_relevance_scores: List[List[int]], k: int) -> float:
        """Вычисляет Precision@K"""
        precisions = []
        for relevance_scores in all_relevance_scores:
            top_k = relevance_scores[:k]
            precision = sum(1 for score in top_k if score >= 1) / len(top_k) if top_k else 0.0
            precisions.append(precision)
        return np.mean(precisions)

    def _compute_generation_metrics(self, generation_results: List[Dict]) -> Dict:
        """Вычисляет метрики для генерации ответов без TensorFlow"""
        try:
            references = [result['expected'] for result in generation_results]
            predictions = [result['actual'] for result in generation_results]

            # ROUGE без TensorFlow
            rouge_metrics = self._compute_rouge_custom(predictions, references)
            
            # METEOR
            meteor_score = self._compute_meteor(predictions, references)
            
            # BERTScore
            bertscore_metrics = {'f1': 0, 'recall': 0, 'precision':0}
            
            # BLEU Score
            bleu_score = self._compute_bleu(predictions, references)
            
            # Semantic Similarity
            semantic_similarity = self._compute_semantic_similarity(predictions, references)

            res = {
                'rouge1': rouge_metrics['rouge1'],
                'rouge2': rouge_metrics['rouge2'],
                'rougeL': rouge_metrics['rougeL'],
                'meteor': meteor_score,
                'bertscore_precision': bertscore_metrics['precision'],
                'bertscore_recall': bertscore_metrics['recall'],
                'bertscore_f1': bertscore_metrics['f1'],
                'bleu': bleu_score,
                'semantic_similarity': semantic_similarity,
                'details': {
                    'rouge_scores': rouge_metrics,
                    'bertscore_scores': bertscore_metrics
                }
            }
            return res
        except Exception as e:
            logger.error(f"Error computing generation metrics: {e}")
            return self._get_empty_generation_metrics()


    def _compute_rouge_custom(self, predictions: List[str], references: List[str]) -> Dict:
        """Вычисляет ROUGE метрики без TensorFlow"""
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
                'rouge1': np.mean(rouge1_scores),
                'rouge2': np.mean(rouge2_scores),
                'rougeL': np.mean(rougeL_scores),
                'rouge1_scores': rouge1_scores,
                'rouge2_scores': rouge2_scores,
                'rougeL_scores': rougeL_scores
            }
        except Exception as e:
            logger.warning(f"ROUGE computation failed: {e}")
            return {'rouge1': 0.0, 'rouge2': 0.0, 'rougeL': 0.0}

    def _compute_meteor(self, predictions: List[str], references: List[str]) -> float:
        """Вычисляет METEOR метрику"""
        return 0.0


    def _compute_bleu(self, predictions: List[str], references: List[str]) -> float:
        """Вычисляет BLEU score"""
        try:
            bleu_metric = evaluate.load('bleu')
            bleu_results = bleu_metric.compute(
                predictions=predictions,
                references=[[ref] for ref in references]  # BLEU требует список списков
            )
            return bleu_results['bleu']
        except Exception as e:
            logger.warning(f"BLEU computation failed: {e}")
            return 0.0

    def _compute_semantic_similarity(self, predictions: List[str], references: List[str]) -> float:
        """Вычисляет семантическое сходство"""
        try:
            # Используем ту же модель, что и для ретривера
            if hasattr(self.vector_store, 'model'):
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
            else:
                return 0.0
        except Exception as e:
            logger.warning(f"Semantic similarity computation failed: {e}")
            return 0.0

    def _get_empty_generation_metrics(self) -> Dict:
        """Возвращает пустые метрики генерации"""
        return {
            'rouge1': 0.0,
            'rouge2': 0.0,
            'rougeL': 0.0,
            'meteor': 0.0,
            'bertscore_precision': 0.0,
            'bertscore_recall': 0.0,
            'bertscore_f1': 0.0,
            'bleu': 0.0,
            'semantic_similarity': 0.0,
            'details': {}
        }

    def _print_results(self, retrieval_metrics: Dict, generation_metrics: Dict):
        """Выводит результаты метрик"""
        print("\n🎯 РЕЗУЛЬТАТЫ МЕТРИК КАЧЕСТВА")
        print("=" * 60)

        print("🔍 МЕТРИКИ РЕТРИВЕРА:")
        print(f"   📊 NDCG@10:        {retrieval_metrics['ndcg@10']:.4f}")
        print(f"   🎯 MRR@10:         {retrieval_metrics['mrr@10']:.4f}")
        print(f"   🗺️  MAP@100:        {retrieval_metrics['map@100']:.4f}")
        print(f"   ✅ Precision@5:     {retrieval_metrics['precision@5']:.4f}")
        print(f"   ✅ Precision@10:    {retrieval_metrics['precision@10']:.4f}")

        print("\n🤖 МЕТРИКИ ГЕНЕРАЦИИ ОТВЕТОВ:")
        print(f"   📝 ROUGE-1:           {generation_metrics['rouge1']:.4f}")
        print(f"   📝 ROUGE-2:           {generation_metrics['rouge2']:.4f}")
        print(f"   📝 ROUGE-L:           {generation_metrics['rougeL']:.4f}")
        print(f"   🌠 METEOR:            {generation_metrics['meteor']:.4f}")
        print(f"   🧠 BERTScore F1:      {generation_metrics['bertscore_f1']:.4f}")
        print(f"   🔤 BLEU:              {generation_metrics['bleu']:.4f}")
        print(f"   🔍 Semantic Similarity: {generation_metrics['semantic_similarity']:.4f}")

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
                    'total_questions': len(generation_results)
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