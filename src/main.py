import os
import sys

# Настраиваем пути для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.qa_system import TransneftQASystem
from scripts.setup_system import setup_complete_system
from scripts.evaluate_benchmark import BenchmarkEvaluator


def demonstrate_qa_system():
    """Демонстрация работы QA-системы"""
    print("🎯 КЕЙС 3: QA-СИСТЕМА ДЛЯ ПАО «ТРАНСНЕФТЬ»")
    print("=" * 60)

    try:
        system = TransneftQASystem()

        # Демонстрационные вопросы
        demo_questions = [
            "Сколько акций в уставном капитале ПАО «Транснефть»?",
            "Когда была зарегистрирована компания?",
            "Какие основные направления деятельности?",
            "Кто является аудитором компании?",
            "Какие проекты реализует Транснефть?",
            "Кто держатель реестра акционеров?"
        ]

        print("\n🧪 ДЕМОНСТРАЦИЯ РАБОТЫ СИСТЕМЫ:")
        print("-" * 50)

        for i, question in enumerate(demo_questions, 1):
            print(f"\n{i}. ❓ ВОПРОС: {question}")
            answer = system.answer_question(question)
            print(f"   💡 ОТВЕТ: {answer}")

            stats = system.get_search_stats(question)
            print(f"   📊 Найдено результатов: {stats['results_found']}")

        print("\n" + "=" * 60)
        print("✅ СИСТЕМА УСПЕШНО ПРОТЕСТИРОВАНА!")

        return system

    except Exception as e:
        print(f"❌ Ошибка демонстрации: {e}")
        return None


def interactive_mode(system):
    """Интерактивный режим QA-системы"""
    print("\n💬 ИНТЕРАКТИВНЫЙ РЕЖИМ")
    print("Задавайте вопросы о ПАО «Транснефть»")
    print("Для возврата в меню введите 'меню'")

    while True:
        try:
            question = input("\n❓ Ваш вопрос: ").strip()

            if question.lower() in ['меню', 'menu', 'выход', 'exit']:
                break

            if question:
                answer = system.answer_question(question)
                print(f"💡 {answer}")
        except KeyboardInterrupt:
            print("\n\n👋 Возврат в меню...")
            break
        except Exception as e:
            print(f"❌ Ошибка: {e}")


def show_system_info():
    """Показывает информацию о системе"""
    try:
        system = TransneftQASystem()
        info = system.get_system_info()

        print("\n📋 ИНФОРМАЦИЯ О СИСТЕМЕ:")
        print("-" * 40)
        print(f"🏢 Статус: {info['status']}")
        print(f"🔧 Модель: {info['model']}")
        print(f"📊 Chunks: {info['total_chunks']}")
        print(f"🎯 Подход: {info['retrieval_engine']}")
        print(f"📈 Порог схожести: {info['similarity_threshold']}")

        # Проверяем соединение
        if system.test_connection():
            print("🔗 Соединение: ✅ Активно")
        else:
            print("🔗 Соединение: ❌ Проблемы")

    except Exception as e:
        print(f"❌ Не удалось получить информацию о системе: {e}")


def show_menu():
    """Главное меню управления кейсом 3"""
    system = None

    while True:
        print("\n" + "=" * 60)
        print("🤖 УПРАВЛЕНИЕ КЕЙСОМ 3: QA-СИСТЕМА ПАО «ТРАНСНЕФТЬ»")
        print("=" * 60)
        print("1. 🛠️  Настроить систему (запустить первый раз)")
        print("2. 🚀 Запустить демонстрацию")
        print("3. 📊 Оценить качество на бенчмарке")
        print("4. 📈 Оценить метрики качества (BLEURT, ROUGE, NDCG, etc.)")
        print("5. 💬 Интерактивный режим")
        print("6. 📋 Информация о системе")
        print("0. 🚪 Выход")
        print("-" * 60)

        try:
            choice = input("Выберите действие: ").strip()

            if choice == "1":
                print("\n🛠️  ЗАПУСК НАСТРОЙКИ СИСТЕМЫ...")
                success = setup_complete_system()
                if success:
                    print("✅ Система успешно настроена!")
                else:
                    print("❌ Ошибка настройки системы!")

            elif choice == "2":
                system = demonstrate_qa_system()

            elif choice == "3":
                print("\n📊 ЗАПУСК ОЦЕНКИ КАЧЕСТВА...")
                try:
                    evaluator = BenchmarkEvaluator()
                    accuracy = evaluator.evaluate_system()
                    if accuracy >= 0.8:
                        print("🎉 ВЫСОКОЕ КАЧЕСТВО СИСТЕМЫ!")
                except Exception as e:
                    print(f"❌ Ошибка оценки: {e}")
            elif choice == "4":
                print("\n📈 ЗАПУСК ОЦЕНКИ МЕТРИК КАЧЕСТВА...")
                try:
                    from scripts.evaluate_metrics import MetricsEvaluator
                    evaluator = MetricsEvaluator()
                    metrics = evaluator.evaluate_all_metrics()
                    print("✅ Метрики успешно вычислены!")
                except Exception as e:
                    print(f"❌ Ошибка оценки метрик: {e}")
            elif choice == "5":
                if system is None:
                    try:
                        system = TransneftQASystem()
                    except Exception as e:
                        print(f"❌ Не удалось инициализировать систему: {e}")
                        continue
                interactive_mode(system)

            elif choice == "6":
                show_system_info()

            elif choice == "0":
                print("👋 Завершение работы...")
                break

            else:
                print("❌ Неверный выбор! Попробуйте снова.")

        except KeyboardInterrupt:
            print("\n\n👋 Завершение работы...")
            break
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")


def main():
    """Главная функция запуска"""
    print("🚀 ЗАПУСК КЕЙСА 3: QA-СИСТЕМА ДЛЯ ПАО «ТРАНСНЕФТЬ»")
    print("Цифровой консультант для ответов на вопросы о компании")
    print("Версия 1.0 | Хакатон «Транснефть — Технологии»")

    show_menu()


if __name__ == "__main__":
    main()