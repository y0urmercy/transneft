import os
import sys
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, src_root)

from data_preparation.document_parser import DocumentParser
from data_preparation.chunker import SemanticChunker
from data_preparation.benchmark_creator import BenchmarkCreator
from core.vector_store import VectorStore
from utils.config import DOCUMENT_PATH, VECTOR_STORE_DIR


def setup_complete_system():

    if not os.path.exists(DOCUMENT_PATH):
        print(f"Документ не найден: {DOCUMENT_PATH}")
        print("Поместите файл .docx в src/data/raw/")
        return False

    try:
        parser = DocumentParser()
        elements = parser.parse_document(DOCUMENT_PATH)

        if not elements:
            print("Не удалось распарсить документ")
            return False

        parser.analyze_document(elements)
        chunker = SemanticChunker()
        chunks = chunker.create_chunks(elements)

        if not chunks:
            print("Не удалось создать chunks")
            return False

        chunker.analyze_chunks(chunks)

        vector_store = VectorStore()
        vector_store.create_embeddings(chunks)
        vector_store.save_index(VECTOR_STORE_DIR)

        benchmark_creator = BenchmarkCreator()
        benchmark = benchmark_creator.create_complete_benchmark()

        if benchmark:
            benchmark_creator.analyze_benchmark(benchmark)

        print("\nЗапуск системы")

        return True

    except Exception as e:
        print(f"Ошибка настройки: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = setup_complete_system()
    if not success:
        sys.exit(1)