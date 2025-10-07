import os
import sys
import json
from typing import List, Dict

# Добавляем путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, src_root)

from core.qa_system import TransneftQASystem
from utils.config import BENCHMARK_PATH


class BenchmarkEvaluator:
    """Оценка QA-системы на бенчмарке"""

    def __init__(self):
        try:
            self.qa_system = TransneftQASystem()
            self.results = []
        except Exception as e:
            print(f"❌ Ошибка инициализации QA системы: {e}")
            raise

    def evaluate_system(self, benchmark_path: str = BENCHMARK_PATH) -> float:
        """Оценивает систему на всем бенчмарке"""
        print("🎯 ОЦЕНКА КАЧЕСТВА QA-СИСТЕМЫ")
        print("=" * 50)

        # Загружаем бенчмарк
        benchmark = self._load_benchmark(benchmark_path)
        if not benchmark:
            return 0.0

        print(f"🧪 Тестирование на {len(benchmark)} вопросах...")

        correct_answers = 0

        for i, item in enumerate(benchmark):
            question = item['question']
            expected_answer = item['answer']

            print(f"   {i + 1:2d}. {question[:50]}...", end=" ")

            # Получаем ответ системы
            system_answer = self.qa_system.answer_question(question)

            # Проверяем корректность
            is_correct = self._check_answer_quality(system_answer, expected_answer, question)

            if is_correct:
                correct_answers += 1
                print("✅")
            else:
                print("❌")

            # Сохраняем результат
            self.results.append({
                'id': item['triplet_id'],
                'question': question,
                'expected': expected_answer,
                'actual': system_answer,
                'is_correct': is_correct,
                'category': item['metadata']['content_type']
            })

        # Вычисляем точность
        accuracy = correct_answers / len(benchmark)

        # Показываем результаты
        self._show_results(accuracy, len(benchmark), correct_answers)

        # Сохраняем детальные результаты
        self._save_results()

        return accuracy

    def _load_benchmark(self, benchmark_path: str) -> List[Dict]:
        """Загружает бенчмарк"""
        try:
            with open(benchmark_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Бенчмарк не найден: {benchmark_path}")
            return []
        except Exception as e:
            print(f"❌ Ошибка загрузки бенчмарка: {e}")
            return []

    def _check_answer_quality(self, system_answer: str, expected_answer: str, question: str) -> bool:
        """Проверяет качество ответа"""
        system_lower = system_answer.lower()
        expected_lower = expected_answer.lower()
        question_lower = question.lower()

        # Ключевые факты для проверки
        key_facts = {
            'акци': ['724 934 300'],
            'зарегистрирована': ['26.08.1993', '1993'],
            'аудитор': ['кэпт'],
            'держатель реестра': ['нрк', 'р.о.с.т.'],
            'направления деятельности': ['транспортировка', 'нефти', 'трубопровод'],
            'протяженность': ['67 000', '67000']
        }

        # Проверяем ключевые факты в зависимости от вопроса
        for key, facts in key_facts.items():
            if key in question_lower:
                for fact in facts:
                    if fact in expected_lower and fact not in system_lower:
                        return False
                return True

        # Общая проверка - если ответ содержит существенную часть ожидаемого
        common_words = set(system_lower.split()) & set(expected_lower.split())
        return len(common_words) >= min(2, len(expected_lower.split()) // 2)

    def _show_results(self, accuracy: float, total: int, correct: int):
        """Показывает результаты оценки"""
        print(f"\n📈 РЕЗУЛЬТАТЫ ОЦЕНКИ:")
        print(f"   📊 Всего вопросов: {total}")
        print(f"   ✅ Правильных ответов: {correct}")
        print(f"   🎯 Точность: {accuracy:.1%}")

        # Анализ по категориям
        self._analyze_by_category()

        print("\n" + "=" * 50)
        if accuracy >= 0.9:
            print("🎉 ОТЛИЧНОЕ КАЧЕСТВО! Максимальный балл обеспечен!")
        elif accuracy >= 0.8:
            print("✅ ВЫСОКОЕ КАЧЕСТВО! Хорошие шансы на максимальный балл!")
        elif accuracy >= 0.7:
            print("⚠️  УДОВЛЕТВОРИТЕЛЬНОЕ КАЧЕСТВО")
        else:
            print("❌ ТРЕБУЕТСЯ ДОРАБОТКА")

    def _analyze_by_category(self):
        """Анализирует результаты по категориям"""
        from collections import defaultdict
        category_stats = defaultdict(lambda: {'total': 0, 'correct': 0})

        for result in self.results:
            category = result['category']
            category_stats[category]['total'] += 1
            if result['is_correct']:
                category_stats[category]['correct'] += 1

        print(f"\n📊 РЕЗУЛЬТАТЫ ПО КАТЕГОРИЯМ:")
        for category, stats in sorted(category_stats.items()):
            accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
            print(f"   {category}: {stats['correct']}/{stats['total']} ({accuracy:.1%})")

    def _save_results(self):
        """Сохраняет детальные результаты"""
        try:
            results_dir = os.path.join(src_root, "evaluation")
            os.makedirs(results_dir, exist_ok=True)

            results_path = os.path.join(results_dir, "benchmark_evaluation_results.json")
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

            print(f"💾 Детальные результаты сохранены: {results_path}")
        except Exception as e:
            print(f"❌ Ошибка сохранения результатов: {e}")


def main():
    """Запуск оценки системы"""
    try:
        evaluator = BenchmarkEvaluator()
        accuracy = evaluator.evaluate_system()

        # Возвращаем код выхода для CI/CD
        sys.exit(0 if accuracy >= 0.7 else 1)

    except Exception as e:
        print(f"❌ Критическая ошибка оценки: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()