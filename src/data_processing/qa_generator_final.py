# scripts/qa_generator_final.py
import json
import re
from typing import List, Dict


def create_final_qa_pairs(chunks: List[Dict]) -> List[Dict]:
    """Создает финальные качественные QA пары"""
    qa_pairs = []

    question_templates = {
        'company_info': [
            "Когда была основана компания {company}?",
            "Какие основные направления деятельности {company}?",
            "Какой уставный капитал {company}?",
            "Кто является акционером {company}?",
            "Где находится головной офис {company}?"
        ],
        'projects': [
            "Что представляет собой проект {project}?",
            "Какие цели у проекта {project}?",
            "Когда был реализован проект {project}?",
            "Какая протяженность {project}?",
            "Какая пропускная способность {project}?"
        ],
        'facts': [
            "Сколько {entity} у компании?",
            "Какова {metric} компании?",
            "Кто является {role} компании?",
            "Когда {event} произошло?",
            "Где находится {location}?"
        ]
    }

    for chunk in chunks:
        context = chunk['text']
        chunk_id = chunk['metadata']['chunk_id']
        sections = chunk['metadata']['sections']

        # Определяем тип контента
        content_type = classify_content(context, sections)

        # Генерируем соответствующие вопросы
        questions = generate_typed_questions(context, content_type, question_templates)

        for question in questions:
            qa_pair = {
                "context": context,
                "question": question,
                "answer": "[Требуется генерация ответа]",
                "chunk_id": chunk_id,
                "sections": sections,
                "content_type": content_type,
                "metadata": chunk['metadata']
            }
            qa_pairs.append(qa_pair)

    return qa_pairs


def classify_content(text: str, sections: List[str]) -> str:
    """Классифицирует тип контента"""
    text_lower = text.lower()
    sections_lower = [s.lower() for s in sections]

    if any(keyword in text_lower for keyword in ['проект', 'строительство', 'трубопровод', 'магистраль']):
        return 'projects'
    elif any(keyword in text_lower for keyword in ['основан', 'учрежден', 'создан', 'дата регистрации']):
        return 'company_info'
    elif any(keyword in text_lower for keyword in ['акци', 'капитал', 'акционер', 'реестр']):
        return 'company_info'
    elif any(keyword in sections_lower for keyword in ['факты', 'история', 'информация']):
        return 'facts'
    else:
        return 'facts'


def generate_typed_questions(text: str, content_type: str, templates: Dict) -> List[str]:
    """Генерирует вопросы по типу контента"""
    questions = []

    if content_type == 'company_info':
        # Вопросы о компании
        company_variants = ["Транснефть", "компании Транснефть", "ПАО Транснефть"]
        for template in templates['company_info']:
            for company in company_variants:
                questions.append(template.format(company=company))

    elif content_type == 'projects':
        # Вопросы о проектах
        projects = extract_projects(text)
        for project in projects[:2]:  # Максимум 2 проекта на chunk
            for template in templates['projects'][:2]:
                questions.append(template.format(project=project))

    else:  # facts
        # Фактологические вопросы
        entities = extract_entities(text)
        for entity in entities[:2]:
            for template in templates['facts'][:2]:
                if '{entity}' in template:
                    questions.append(template.format(entity=entity))
                elif '{metric}' in template:
                    questions.append(template.format(metric=entity))
                elif '{role}' in template:
                    questions.append(template.format(role=entity))
                elif '{event}' in template:
                    questions.append(template.format(event=entity))
                elif '{location}' in template:
                    questions.append(template.format(location=entity))

    return list(set(questions))[:3]  # Убираем дубли и ограничиваем 3 вопросами


def extract_projects(text: str) -> List[str]:
    """Извлекает названия проектов"""
    projects = []

    # Ищем проекты в кавычках
    quoted_projects = re.findall(r'[«"]([^»"]+?)[»"]', text)
    projects.extend(quoted_projects)

    # Ищем упоминания проектов
    project_keywords = re.findall(r'(проект\s+[«"][^»"]+[»"]|проект\s+[А-Я][^.!?]{0,50})', text)
    projects.extend([p.strip() for p in project_keywords])

    return projects


def extract_entities(text: str) -> List[str]:
    """Извлекает ключевые сущности"""
    entities = []

    # Числовые данные
    numbers = re.findall(r'(\d+(?:\.\d+)?\s*(?:млн|тыс|км|тонн|рублей|акций|год))', text)
    entities.extend(numbers)

    # Даты
    dates = re.findall(r'(\d{1,2}\.\d{2}\.\d{4}|\d{4}\s*год)', text)
    entities.extend(dates)

    # Организации и должности
    orgs = re.findall(r'([А-Я][а-я]+\s+[А-Я][а-я]+\s+(?:компания|общество|агентство|департамент))', text)
    entities.extend(orgs)

    return entities


if __name__ == "__main__":
    try:
        # Загружаем chunks
        with open("data/processed/document_chunks.json", "r", encoding="utf-8") as f:
            chunks = json.load(f)

        print(f"Загружено {len(chunks)} chunks")

        # Создаем финальные QA пары
        print("Создание финальных QA пар...")
        qa_pairs = create_final_qa_pairs(chunks)

        # Сохраняем результат
        with open("data/processed/qa_benchmark_final.json", "w", encoding="utf-8") as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)

        print(f"✅ Сгенерировано {len(qa_pairs)} финальных QA пар")
        print("✅ Бенчмарк сохранен в data/processed/qa_benchmark_final.json")

        # Анализируем типы вопросов
        content_types = {}
        for pair in qa_pairs:
            content_type = pair['content_type']
            content_types[content_type] = content_types.get(content_type, 0) + 1

        print("\n📊 Распределение вопросов по типам:")
        for content_type, count in content_types.items():
            print(f"  - {content_type}: {count}")

        # Показываем примеры
        print("\n🔍 Примеры финальных QA пар:")
        for i, pair in enumerate(qa_pairs[:5]):
            print(f"\n--- Пример {i + 1} ({pair['content_type']}) ---")
            print(f"Вопрос: {pair['question']}")
            print(f"Разделы: {pair['sections']}")

    except FileNotFoundError:
        print("❌ Файл с chunks не найден. Сначала запустите doc_parser.py")
    except Exception as e:
        print(f"❌ Ошибка: {e}")