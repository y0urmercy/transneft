import os
import sys
import docx
import re
import json
from typing import List, Dict

# Добавляем путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, src_root)

from utils.config import SECTION_HEADERS, ELEMENTS_PATH


class DocumentParser:
    """Парсер документов .docx для ПАО «Транснефть»"""

    def __init__(self):
        self.section_headers = SECTION_HEADERS

    def parse_document(self, doc_path: str) -> List[Dict]:
        """Парсит .docx документ и извлекает структурированные элементы"""
        print(" Начало парсинга документа...")

        try:
            if not os.path.exists(doc_path):
                raise FileNotFoundError(f"Документ не найден: {doc_path}")

            doc = docx.Document(doc_path)
            elements = []
            current_section = "Основная информация"
            element_id = 0

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    continue

                # Определяем тип элемента
                element_type = self._classify_element(text, paragraph.style.name)

                # Обновляем текущий раздел для заголовков
                if element_type == "section_header":
                    current_section = text

                # Создаем элемент
                element = {
                    'element_id': element_id,
                    'type': element_type,
                    'text': text,
                    'section': current_section,
                    'style': paragraph.style.name,
                    'word_count': len(text.split())
                }

                elements.append(element)
                element_id += 1

            print(f" Документ распарсен: {len(elements)} элементов")

            # Сохраняем элементы
            self._save_elements(elements)

            return elements

        except Exception as e:
            print(f" Ошибка парсинга документа: {e}")
            return []

    def _classify_element(self, text: str, style: str) -> str:
        """Классифицирует тип элемента документа"""

        # Заголовки разделов
        if any(header.lower() in text.lower() for header in self.section_headers):
            return "section_header"

        # Стилевые заголовки
        if style and 'heading' in style.lower():
            return "section_header"

        # Годы (1990, 2000 и т.д.)
        if re.match(r'^\d{3,4}\.?$', text.strip()):
            return "year_header"

        # Нумерованные списки
        if re.match(r'^\d+[\.\)]', text.strip()):
            return "numbered_item"

        # Маркированные списки
        if text.strip().startswith(('-', '•', '—')):
            return "bullet_item"

        # Проекты
        if re.search(r'[Пп]роект|[Сс]троительство', text) and len(text) < 150:
            return "project_header"

        # Основной текст
        return "paragraph"

    def _save_elements(self, elements: List[Dict]):
        """Сохраняет элементы в файл"""
        try:
            with open(ELEMENTS_PATH, 'w', encoding='utf-8') as f:
                json.dump(elements, f, ensure_ascii=False, indent=2)
            print(f" Элементы сохранены: {ELEMENTS_PATH}")
        except Exception as e:
            print(f" Ошибка сохранения элементов: {e}")

    def analyze_document(self, elements: List[Dict]):
        """Анализирует структуру документа"""
        print("\n АНАЛИЗ ДОКУМЕНТА:")
        print("-" * 40)

        total_elements = len(elements)
        sections = set()
        element_types = {}

        for elem in elements:
            sections.add(elem['section'])
            elem_type = elem['type']
            element_types[elem_type] = element_types.get(elem_type, 0) + 1

        print(f" Всего элементов: {total_elements}")
        print(f" Разделов: {len(sections)}")
        print(" Типы элементов:")
        for elem_type, count in element_types.items():
            percentage = (count / total_elements) * 100
            print(f"   - {elem_type}: {count} ({percentage:.1f}%)")

        # Показываем основные разделы
        print("\n Основные разделы:")
        for i, section in enumerate(list(sections)[:10]):
            print(f"   {i + 1}. {section}")


if __name__ == "__main__":
    from utils.config import DOCUMENT_PATH

    parser = DocumentParser()
    elements = parser.parse_document(DOCUMENT_PATH)
    if elements:
        parser.analyze_document(elements)