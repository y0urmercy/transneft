import os
import sys
import json
from typing import List, Dict

# Добавляем путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, src_root)

from utils.config import MAX_CHUNK_SIZE, MIN_CHUNK_SIZE, MAX_WORDS_PER_CHUNK, CHUNKS_PATH


class SemanticChunker:
    """Семантическое чанкование с сохранением логических блоков"""

    def __init__(self):
        self.max_chunk_size = MAX_CHUNK_SIZE
        self.min_chunk_size = MIN_CHUNK_SIZE
        self.max_words = MAX_WORDS_PER_CHUNK

    def create_chunks(self, elements: List[Dict]) -> List[Dict]:
        """Создает семантические chunks из элементов"""
        print("️  Начало семантического чанкования...")

        chunks = []
        current_chunk = []
        current_word_count = 0
        current_section = "Основная информация"

        for element in elements:
            text = element['text']
            words = text.split()
            word_count = len(words)

            # Проверяем начало нового раздела
            if self._should_start_new_chunk(element, current_chunk, current_word_count):
                if current_chunk and current_word_count >= self.min_chunk_size:
                    chunks.append(self._create_chunk(current_chunk, len(chunks)))

                current_chunk = [element]
                current_word_count = word_count
                current_section = element.get('section', current_section)
                continue

            # Проверяем не превысили ли лимит
            if current_word_count + word_count > self.max_words and current_chunk:
                chunks.append(self._create_chunk(current_chunk, len(chunks)))
                current_chunk = [element]
                current_word_count = word_count
            else:
                current_chunk.append(element)
                current_word_count += word_count

        # Добавляем последний chunk
        if current_chunk and current_word_count >= self.min_chunk_size:
            chunks.append(self._create_chunk(current_chunk, len(chunks)))

        print(f" Создано {len(chunks)} семантических chunks")

        # Сохраняем chunks
        self._save_chunks(chunks)

        return chunks

    def _should_start_new_chunk(self, element: Dict, current_chunk: List, current_word_count: int) -> bool:
        """Определяет, нужно ли начинать новый chunk"""
        element_type = element['type']

        # Заголовки разделов всегда начинают новые chunks
        if element_type == "section_header":
            return True

        # Годы начинают новые chunks если текущий chunk достаточно большой
        if element_type == "year_header" and current_word_count >= self.min_chunk_size:
            return True

        # Проекты начинают новые chunks
        if element_type == "project_header" and current_word_count >= self.min_chunk_size:
            return True

        return False

    def _create_chunk(self, elements: List[Dict], chunk_id: int) -> Dict:
        """Создает объект chunk из элементов"""
        chunk_text = "\n".join([elem['text'] for elem in elements])

        # Собираем метаданные
        sections = list(set([elem['section'] for elem in elements]))
        element_types = list(set([elem['type'] for elem in elements]))
        word_count = len(chunk_text.split())

        # Определяем структурированность
        is_structured = any(elem['type'] in ['numbered_item', 'bullet_item'] for elem in elements)

        metadata = {
            'chunk_id': chunk_id,
            'sections': sections,
            'element_types': element_types,
            'num_elements': len(elements),
            'word_count': word_count,
            'is_structured': is_structured,
            'has_header': any(elem['type'] == 'section_header' for elem in elements)
        }

        return {
            'text': chunk_text,
            'metadata': metadata,
            'elements': [elem['element_id'] for elem in elements]
        }

    def _save_chunks(self, chunks: List[Dict]):
        """Сохраняет chunks в файл"""
        try:
            with open(CHUNKS_PATH, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            print(f" Chunks сохранены: {CHUNKS_PATH}")
        except Exception as e:
            print(f" Ошибка сохранения chunks: {e}")

    def analyze_chunks(self, chunks: List[Dict]):
        """Анализирует полученные chunks"""
        print("\n АНАЛИЗ CHUNKS:")
        print("-" * 40)

        total_chunks = len(chunks)
        total_words = sum(chunk['metadata']['word_count'] for chunk in chunks)
        structured_chunks = sum(1 for chunk in chunks if chunk['metadata']['is_structured'])

        print(f" Всего chunks: {total_chunks}")
        print(f" Всего слов: {total_words}")
        print(f" Средний размер: {total_words / total_chunks:.1f} слов/chunk")
        print(f"️  Структурированных chunks: {structured_chunks} ({structured_chunks / total_chunks:.1%})")

        # Распределение по размерам
        size_ranges = {'small': 0, 'medium': 0, 'large': 0}
        for chunk in chunks:
            words = chunk['metadata']['word_count']
            if words < 100:
                size_ranges['small'] += 1
            elif words < 250:
                size_ranges['medium'] += 1
            else:
                size_ranges['large'] += 1

        print("\n Распределение по размерам:")
        for size, count in size_ranges.items():
            percentage = (count / total_chunks) * 100
            print(f"   - {size}: {count} chunks ({percentage:.1f}%)")


if __name__ == "__main__":
    from utils.config import ELEMENTS_PATH

    chunker = SemanticChunker()

    with open(ELEMENTS_PATH, 'r', encoding='utf-8') as f:
        elements = json.load(f)

    chunks = chunker.create_chunks(elements)
    chunker.analyze_chunks(chunks)