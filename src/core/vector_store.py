import os
import sys
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import torch
from typing import List, Dict, Tuple

current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, src_root)

from utils.config import MODEL_NAME, VECTOR_STORE_DIR, EMBEDDING_DIMENSION


class VectorStore:
    def __init__(self, model_name: str = MODEL_NAME):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 Инициализация VectorStore на {self.device}")

        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            self.index = None
            self.chunks = []
            self.chunk_metadata = []
            self.is_initialized = False
        except Exception as e:
            print(f"❌ Ошибка инициализации модели: {e}")
            raise

    def create_embeddings(self, chunks: List[Dict]) -> None:
        print("📥 Создание эмбеддингов...")

        if not chunks:
            raise ValueError("❌ Нет chunks для обработки")

        self.chunks = [chunk['text'] for chunk in chunks]
        self.chunk_metadata = [chunk['metadata'] for chunk in chunks]

        try:
            # Создаем эмбеддинги с прогресс-баром
            embeddings = self.model.encode(
                self.chunks,
                batch_size=16,
                show_progress_bar=True,
                convert_to_tensor=True,
                normalize_embeddings=True
            )

            # Конвертируем в numpy
            embeddings_np = embeddings.cpu().numpy() if self.device == "cuda" else embeddings.numpy()

            # Создаем FAISS индекс для косинусного сходства
            self.index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
            self.index.add(embeddings_np)

            self.is_initialized = True
            print(f"✅ Векторное хранилище создано: {self.index.ntotal} векторов")

        except Exception as e:
            print(f"❌ Ошибка создания эмбеддингов: {e}")
            raise

    def search(self, query: str, k: int = 5, threshold: float = 0.3) -> List[Tuple[str, Dict, float]]:
        if not self.is_initialized or self.index is None:
            raise ValueError("❌ Индекс не инициализирован. Сначала вызовите create_embeddings()")

        if not query or not query.strip():
            return []

        try:
            query_embedding = self.model.encode(
                [query],
                convert_to_tensor=True,
                normalize_embeddings=True
            )

            query_embedding_np = query_embedding.cpu().numpy() if self.device == "cuda" else query_embedding.numpy()

            scores, indices = self.index.search(query_embedding_np, k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.chunks) and score >= threshold:
                    results.append((
                        self.chunks[idx],
                        self.chunk_metadata[idx],
                        float(score)
                    ))

            return results

        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")
            return []

    def save_index(self, save_path: str = VECTOR_STORE_DIR):
        """Сохраняет индекс и метаданные"""
        if not self.is_initialized:
            raise ValueError("❌ Хранилище не инициализировано")
        try:
            os.makedirs(save_path, exist_ok=True)

            if not os.path.exists(save_path):
                raise OSError(f"Не удалось создать директорию: {save_path}")

            test_file = os.path.join(save_path, "test_write.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                raise OSError(f"Нет прав на запись в директорию {save_path}: {e}")

            index_path = os.path.join(save_path, "faiss.index")
            print(f"💾 Сохранение FAISS индекса: {index_path}")
            faiss.write_index(self.index, index_path)

            chunks_path = os.path.join(save_path, "chunks.json")
            metadata_path = os.path.join(save_path, "metadata.json")
            model_info_path = os.path.join(save_path, "model_info.json")

            with open(chunks_path, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=2)

            model_info = {
                "model_name": MODEL_NAME,
                "embedding_dimension": EMBEDDING_DIMENSION,
                "total_vectors": self.index.ntotal,
                "device": self.device
            }

            with open(model_info_path, "w", encoding="utf-8") as f:
                json.dump(model_info, f, ensure_ascii=False, indent=2)

            print(f"✅ Векторное хранилище сохранено: {save_path}")

        except Exception as e:
            print(f"❌ Ошибка сохранения векторного хранилища: {e}")

            print("🔄 Попытка сохранения в альтернативную директорию...")
            self._save_to_alternative_location()

    def _save_to_alternative_location(self):
        """Сохраняет в альтернативную директорию при ошибках"""
        try:
            alt_path = "vector_store_temp"
            os.makedirs(alt_path, exist_ok=True)

            faiss.write_index(self.index, f"{alt_path}/faiss.index")

            with open(f"{alt_path}/chunks.json", "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)

            with open(f"{alt_path}/metadata.json", "w", encoding="utf-8") as f:
                json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=2)

            print(f"✅ Векторное хранилище сохранено в альтернативную директорию: {alt_path}")
            return alt_path

        except Exception as e:
            print(f"❌ Критическая ошибка: не удалось сохранить векторное хранилище: {e}")
            raise

    def load_index(self, load_path: str = VECTOR_STORE_DIR):
        """Загружает индекс и метаданные"""
        try:
            required_files = [
                os.path.join(load_path, "faiss.index"),
                os.path.join(load_path, "chunks.json"),
                os.path.join(load_path, "metadata.json")
            ]

            for file_path in required_files:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Файл не найден: {file_path}")

            self.index = faiss.read_index(os.path.join(load_path, "faiss.index"))

            with open(os.path.join(load_path, "chunks.json"), "r", encoding="utf-8") as f:
                self.chunks = json.load(f)

            with open(os.path.join(load_path, "metadata.json"), "r", encoding="utf-8") as f:
                self.chunk_metadata = json.load(f)

            self.is_initialized = True
            print(f"📂 Векторное хранилище загружено: {load_path}")
            print(f"📊 Размер: {len(self.chunks)} chunks, {self.index.ntotal} векторов")

        except Exception as e:
            print(f"❌ Ошибка загрузки векторного хранилища: {e}")
            raise

    def get_stats(self) -> Dict:
        if not self.is_initialized:
            return {"error": "Хранилище не инициализировано"}

        return {
            "total_chunks": len(self.chunks),
            "total_vectors": self.index.ntotal,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "device": self.device,
            "model": MODEL_NAME
        }


if __name__ == "__main__":
    from utils.config import CHUNKS_PATH

    with open(CHUNKS_PATH, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    vector_store = VectorStore()
    vector_store.create_embeddings(chunks)
    vector_store.save_index()

    test_queries = [
        "Сколько акций в уставном капитале?",
        "Основные направления деятельности",
        "Дата регистрации компании"
    ]

    print("\n🔍 ТЕСТИРОВАНИЕ ПОИСКА:")
    for query in test_queries:
        print(f"\nЗапрос: '{query}'")
        results = vector_store.search(query, k=2)
        for i, (chunk, metadata, score) in enumerate(results):
            print(f"  {i + 1}. [Score: {score:.3f}] {chunk[:80]}...")
