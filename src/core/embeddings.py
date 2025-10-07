import os
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

class SimpleEmbeddings:
    """Простая реализация эмбеддингов без LangChain"""
    
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🔧 Загрузка модели: {model_name} на {self.device}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
    
    def embed_documents(self, texts):
        """Создает эмбеддинги для списка документов"""
        embeddings = []
        
        for text in texts:
            embedding = self._get_embedding(text)
            embeddings.append(embedding)
        
        return np.array(embeddings)
    
    def embed_query(self, text):
        """Создает эмбеддинг для одного запроса"""
        return self._get_embedding(text)
    
    def _get_embedding(self, text):
        """Внутренний метод для получения эмбеддинга"""
        with torch.no_grad():
            inputs = self.tokenizer(
                text, 
                padding=True, 
                truncation=True, 
                max_length=512, 
                return_tensors="pt"
            ).to(self.device)
            
            outputs = self.model(**inputs)
            embeddings = self._mean_pooling(outputs, inputs['attention_mask'])
            embeddings = F.normalize(embeddings, p=2, dim=1)
            
            return embeddings.cpu().numpy()[0]
    
    def _mean_pooling(self, model_output, attention_mask):
        """Mean pooling для получения sentence embeddings"""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)