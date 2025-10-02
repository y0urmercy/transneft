# scripts/vector_store.py
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import torch
import os
from typing import List, Dict, Tuple


class VectorStore:
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Инициализация модели на устройстве: {self.device}")

        # Загружаем модель для эмбеддингов
        self.model = SentenceTransformer(model_name, device=self.device)
        self.index = None
        self.chunks = []
        self.chunk_metadata = []

    def create_embeddings(self, chunks: List[Dict]) -> None:
        """Создает эмбеддинги для всех chunks"""
        print("Создание эмбеддингов...")

        self.chunks = [chunk['text'] for chunk in chunks]
        self.chunk_metadata = [chunk['metadata'] for chunk in chunks]

        # Создаем эмбеддинги
        embeddings = self.model.encode(
            self.chunks,
            batch_size=8,
            show_progress_bar=True,
            convert_to_tensor=True
        )

        # Конвертируем в numpy для FAISS
        embeddings_np = embeddings.cpu().numpy() if self.device == "cuda" else embeddings.numpy()

        # Создаем FAISS индекс
        dimension = embeddings_np.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product для косинусного сходства

        # Нормализуем векторы для косинусного сходства
        faiss.normalize_L2(embeddings_np)
        self.index.add(embeddings_np)

        print(f"✅ Создан индекс с {self.index.ntotal} векторами")

    def search(self, query: str, k: int = 5) -> List[Tuple[str, Dict, float]]:
        """Поиск наиболее релевантных chunks"""
        if self.index is None:
            raise ValueError("Индекс не инициализирован. Сначала вызовите create_embeddings()")

        # Создаем эмбеддинг для запроса
        query_embedding = self.model.encode([query], convert_to_tensor=True)
        query_embedding_np = query_embedding.cpu().numpy() if self.device == "cuda" else query_embedding.numpy()

        # Нормализуем запрос
        faiss.normalize_L2(query_embedding_np)

        # Выполняем поиск
        scores, indices = self.index.search(query_embedding_np, k)

        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.chunks):  # Проверяем границы
                results.append((
                    self.chunks[idx],
                    self.chunk_metadata[idx],
                    float(score)
                ))

        return results

    def save_index(self, save_path: str = "models/vector_store"):
        """Сохраняет индекс и метаданные"""
        os.makedirs(save_path, exist_ok=True)

        faiss.write_index(self.index, f"{save_path}/faiss.index")

        with open(f"{save_path}/chunks.json", "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)

        with open(f"{save_path}/metadata.json", "w", encoding="utf-8") as f:
            json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=2)

        print(f"✅ Векторное хранилище сохранено в {save_path}")

    def load_index(self, load_path: str = "models/vector_store"):
        """Загружает индекс и метаданные"""
        self.index = faiss.read_index(f"{load_path}/faiss.index")

        with open(f"{load_path}/chunks.json", "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        with open(f"{load_path}/metadata.json", "r", encoding="utf-8") as f:
            self.chunk_metadata = json.load(f)

        print(f"✅ Векторное хранилище загружено из {load_path}")


# Тестируем векторное хранилище
if __name__ == "__main__":
    # Загружаем chunks
    with open("data/processed/document_chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Загружено {len(chunks)} chunks для создания векторного хранилища")

    # Создаем и наполняем векторное хранилище
    vector_store = VectorStore()
    vector_store.create_embeddings(chunks)

    # Сохраняем индекс
    vector_store.save_index()

    # Тестируем поиск
    test_queries = [
        "Когда была основана Транснефть?",
        "Какие основные проекты у компании?",
        "Сколько километров трубопроводов?",
        "Кто является аудитором компании?"
    ]

    print("\n🔍 ТЕСТИРОВАНИЕ ПОИСКА:")
    for query in test_queries:
        print(f"\nЗапрос: '{query}'")
        results = vector_store.search(query, k=3)

        for i, (chunk, metadata, score) in enumerate(results):
            print(f"  {i + 1}. [Score: {score:.3f}] {chunk[:100]}...")