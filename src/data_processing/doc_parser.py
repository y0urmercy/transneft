# scripts/doc_parser.py
import docx
import pandas as pd
import re
import json
import os
from typing import List, Dict
import nltk
from nltk.tokenize import sent_tokenize

# Создаем необходимые папки
os.makedirs("data/processed", exist_ok=True)
os.makedirs("models", exist_ok=True)


class TransneftDocumentParser:
    def __init__(self, doc_path: str):
        self.doc_path = doc_path
        self.doc = docx.Document(doc_path)

    def extract_structured_content(self) -> List[Dict]:
        """Извлекает содержимое с сохранением структуры и семантики"""
        elements = []
        current_section = "Основная информация"

        for i, paragraph in enumerate(self.doc.paragraphs):
            text = paragraph.text.strip()
            if not text:
                continue

            # Определяем тип элемента по стилю и содержанию
            element_type = self._classify_element(text, paragraph.style.name)

            if element_type == "section_header":
                current_section = text

            elements.append({
                'type': element_type,
                'text': text,
                'section': current_section,
                'style': paragraph.style.name,
                'element_id': i
            })

        return elements

    def _classify_element(self, text: str, style: str) -> str:
        """Классифицирует элементы документа"""
        # Заголовки
        if style and 'heading' in style.lower():
            return "section_header"
        if re.match(r'^#+\s', text) or (len(text) < 100 and re.match(r'^[А-Я][А-Я\s]{5,}', text)):
            return "section_header"

        # Годы (исторические даты)
        if re.match(r'^\d{3,4}$', text.strip()):
            return "year_header"

        # Проекты
        if re.match(r'^.*[Пп]роект.*', text) and len(text) < 150:
            return "project_header"

        # Основной текст
        return "paragraph"

    def create_semantic_chunks(self, elements: List[Dict], max_tokens: int = 400) -> List[Dict]:
        """Создает семантические chunks с учетом структуры"""
        chunks = []
        current_chunk = []
        current_tokens = 0

        for element in elements:
            text = element['text']
            words = text.split()

            # Если начинается новый раздел, завершаем текущий chunk
            if element['type'] in ['section_header', 'year_header', 'project_header'] and current_chunk:
                if current_tokens > 50:  # Минимальный размер chunk
                    chunks.append(self._create_chunk_object(current_chunk, len(chunks)))
                current_chunk = []
                current_tokens = 0

            # Если элемент слишком большой, разбиваем его
            if len(words) > 150:
                sentences = sent_tokenize(text)
                for sentence in sentences:
                    sentence_words = sentence.split()
                    if current_tokens + len(sentence_words) > max_tokens and current_chunk:
                        chunks.append(self._create_chunk_object(current_chunk, len(chunks)))
                        current_chunk = []
                        current_tokens = 0

                    current_chunk.append({
                        'text': sentence,
                        'type': element['type'],
                        'section': element['section']
                    })
                    current_tokens += len(sentence_words)
            else:
                if current_tokens + len(words) > max_tokens and current_chunk:
                    chunks.append(self._create_chunk_object(current_chunk, len(chunks)))
                    current_chunk = []
                    current_tokens = 0

                current_chunk.append({
                    'text': text,
                    'type': element['type'],
                    'section': element['section']
                })
                current_tokens += len(words)

        # Добавляем последний chunk
        if current_chunk and current_tokens > 20:
            chunks.append(self._create_chunk_object(current_chunk, len(chunks)))

        return chunks

    def _create_chunk_object(self, elements: List[Dict], chunk_id: int) -> Dict:
        """Создает объект chunk из элементов"""
        chunk_text = "\n".join([elem['text'] for elem in elements])
        metadata = {
            'chunk_id': chunk_id,
            'sections': list(set([elem['section'] for elem in elements])),
            'element_types': list(set([elem['type'] for elem in elements])),
            'num_elements': len(elements),
            'approx_tokens': len(chunk_text.split())
        }

        return {
            'text': chunk_text,
            'metadata': metadata,
            'elements': elements
        }

    def analyze_document_stats(self, elements: List[Dict]):
        """Анализирует статистику документа"""
        total_elements = len(elements)
        sections = set()
        element_types = {}

        for elem in elements:
            sections.add(elem['section'])
            element_types[elem['type']] = element_types.get(elem['type'], 0) + 1

        print("=== АНАЛИЗ ДОКУМЕНТА ===")
        print(f"Всего элементов: {total_elements}")
        print(f"Разделы: {len(sections)}")
        print("Типы элементов:")
        for elem_type, count in element_types.items():
            print(f"  - {elem_type}: {count}")


# Запуск парсера
if __name__ == "__main__":
    parser = TransneftDocumentParser(
        "Реестр данных о компании ПАО Транснефть для хакатона весна-лета 2026.docx")

    print("Извлечение структуры документа...")
    elements = parser.extract_structured_content()

    print("Анализ статистики...")
    parser.analyze_document_stats(elements)

    print("Создание семантических chunks...")
    chunks = parser.create_semantic_chunks(elements)

    # Сохраняем результаты
    with open("data/processed/document_elements.json", "w", encoding="utf-8") as f:
        json.dump(elements, f, ensure_ascii=False, indent=2)

    with open("data/processed/document_chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"✅ Извлечено {len(elements)} элементов")
    print(f"✅ Создано {len(chunks)} chunks")

    # Показываем примеры chunks
    print("\nПримеры chunks:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\n--- Chunk {i + 1} ---")
        print(f"Разделы: {chunk['metadata']['sections']}")
        print(f"Текст: {chunk['text'][:200]}...")
        print(f"Токенов: {chunk['metadata']['approx_tokens']}")