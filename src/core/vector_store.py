import os
import sys
import json
import numpy as np
import faiss
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings("ignore")
current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, src_root)

from utils.config import VECTOR_STORE_DIR
SAFE_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

class SimpleEmbeddings:
    """Простая реализация эмбеддингов без TensorFlow"""
    
    def __init__(self, model_name=SAFE_MODEL_NAME):
        print(f"🔧 Загрузка модели: {model_name}")
        
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            import torch.nn.functional as F
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.tokenizer = AutoTokenizer.from_pretrained(SAFE_MODEL_NAME)
            self.model = AutoModel.from_pretrained(SAFE_MODEL_NAME)
            self.model.to(self.device)
            self.model.eval()
            
            self.torch = torch
            self.F = F
            
        except ImportError as e:
            print(f"Ошибка загрузки transformers: {e}")
            print("Установите: pip install transformers torch")
            raise
    
    def embed_documents(self, texts):
        print(f"Обработка {len(texts)} документов...")
        embeddings = []
        batch_size = 8
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self._embed_batch(batch_texts)
            embeddings.extend(batch_embeddings)
            
            if i % 32 == 0:
                print(f"📊 Обработано {min(i + batch_size, len(texts))}/{len(texts)} документов")
        
        return np.array(embeddings)
    
    def embed_query(self, text):
        return self._embed_batch([text])[0]
    
    def _embed_batch(self, texts):
        with self.torch.no_grad():
            inputs = self.tokenizer(
                texts, 
                padding=True, 
                truncation=True, 
                max_length=512, 
                return_tensors="pt"
            ).to(self.device)
            
            outputs = self.model(**inputs)
            embeddings = self._mean_pooling(outputs, inputs['attention_mask'])
            embeddings = self.F.normalize(embeddings, p=2, dim=1)
            
            return embeddings.cpu().numpy()
    
    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return self.torch.sum(token_embeddings * input_mask_expanded, 1) / self.torch.clamp(input_mask_expanded.sum(1), min=1e-9)


class VectorStore:
    def __init__(self, model_name: str = SAFE_MODEL_NAME):
        print(f"Инициализация VectorStore с моделью: {model_name}")

        try:
            self.embeddings = SimpleEmbeddings(model_name)
            self.index = None
            self.chunks = []
            self.chunk_metadata = []
            self.is_initialized = False
            print("VectorStore инициализирован")
        except Exception as e:
            print(f"Ошибка инициализации VectorStore: {e}")
            raise

    # Остальные методы остаются без изменений...
    def create_embeddings(self, chunks: List[Dict]) -> None:
        if not chunks:
            raise ValueError("Нет chunks для обработки")

        self.chunks = [chunk['text'] for chunk in chunks]
        self.chunk_metadata = [chunk['metadata'] for chunk in chunks]

        try:
            embeddings = self.embeddings.embed_documents(self.chunks)
            embeddings_np = np.array(embeddings).astype('float32')
            self.index = faiss.IndexFlatIP(embeddings_np.shape[1])
            self.index.add(embeddings_np)

            self.is_initialized = True

        except Exception as e:
            print(f"Ошибка создания эмбеддингов: {e}")
            raise

    def search(self, query: str, k: int = 5, threshold: float = 0.3) -> List[Tuple[str, Dict, float]]:
        if not self.is_initialized or self.index is None:
            raise ValueError("Индекс не инициализирован. Сначала вызовите create_embeddings()")

        if not query or not query.strip():
            return []

        try:
            query_embedding = self.embeddings.embed_query(query)
            query_embedding_np = np.array([query_embedding]).astype('float32')
            scores, indices = self.index.search(query_embedding_np, min(k, len(self.chunks)))

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if 0 <= idx < len(self.chunks) and score >= threshold:
                    results.append((
                        self.chunks[idx],
                        self.chunk_metadata[idx],
                        float(score)
                    ))

            return results

        except Exception as e:
            print(f"Ошибка поиска: {e}")
            return []

    def save_index(self, save_path: str = VECTOR_STORE_DIR):
        if not self.is_initialized:
            raise ValueError("Хранилище не инициализировано")
        
        try:
            os.makedirs(save_path, exist_ok=True)

            index_path = os.path.join(save_path, "faiss.index")
            print(f"💾 Сохранение FAISS индекса: {index_path}")
            faiss.write_index(self.index, index_path)

            chunks_path = os.path.join(save_path, "chunks.json")
            metadata_path = os.path.join(save_path, "metadata.json")

            with open(chunks_path, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=2)


        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            raise

    def load_index(self, load_path: str = VECTOR_STORE_DIR):
        try:
            self.index = faiss.read_index(os.path.join(load_path, "faiss.index"))
            with open(os.path.join(load_path, "chunks.json"), "r", encoding="utf-8") as f:
                self.chunks = json.load(f)

            with open(os.path.join(load_path, "metadata.json"), "r", encoding="utf-8") as f:
                self.chunk_metadata = json.load(f)

            self.is_initialized = True

        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            raise

    def get_stats(self) -> Dict:
        if not self.is_initialized:
            return {"error": "Хранилище не инициализировано"}

        return {
            "total_chunks": len(self.chunks),
            "total_vectors": self.index.ntotal,
            "embedding_dimension": self.index.d,
            "device": self.embeddings.device
        }