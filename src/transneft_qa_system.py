import streamlit as st
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import tempfile
import os
import sys

# Добавляем путь к src
sys.path.append('src')

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS, Chroma
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

# Метрики оценки
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu
import evaluate
from bert_score import score as bert_score

# Наши модули
from config import TransneftConfig, get_model_config, validate_benchmark_path
from benchmark_utils import BenchmarkAnalyzer, export_benchmark_report

class TransneftBenchmarkQA:
    """Основной класс QA системы для Транснефть"""
    
    def __init__(self, benchmark_path: str = None):
        self.benchmark_path = benchmark_path or TransneftConfig.BENCHMARK_PATH
        self.benchmark_data = None
        self.vector_store = None
        self.qa_chain = None
        self.embeddings = None
        self.qa_pairs = []
        self.sections = []
        
        # Загрузка бенчмарка
        self.load_benchmark()
        
    def load_benchmark(self):
        """Загрузка бенчмарка"""
        try:
            if not os.path.exists(self.benchmark_path):
                st.error(f"❌ Файл бенчмарка не найден: {self.benchmark_path}")
                return
                
            with open(self.benchmark_path, 'r', encoding='utf-8') as f:
                self.benchmark_data = json.load(f)
            
            self.qa_pairs = self.benchmark_data.get('qa_pairs', [])
            self.sections = self.benchmark_data.get('sections', [])
            
            st.success(f"✅ Бенчмарк загружен: {len(self.qa_pairs)} QA пар, {len(self.sections)} секций")
            
        except Exception as e:
            st.error(f"❌ Ошибка загрузки бенчмарка: {str(e)}")
    
    def initialize_system(self, embedding_model: str = None, search_mode: str = "balanced"):
        """Полная инициализация системы"""
        if not self.benchmark_data:
            raise ValueError("Бенчмарк не загружен")
        
        # Инициализация эмбеддингов
        model_name = embedding_model or TransneftConfig.EMBEDDING_MODELS["default"]
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Подготовка документов
        documents = self.prepare_training_data()
        
        # Создание векторного хранилища
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        
        # Инициализация QA цепи
        self.initialize_qa_chain(search_mode)
        
        return len(documents)
    
    def prepare_training_data(self) -> List[Document]:
        """Подготовка данных для обучения из бенчмарка"""
        documents = []
        
        for qa_pair in self.qa_pairs:
            doc = Document(
                page_content=qa_pair['context'],
                metadata={
                    'section': qa_pair['section'],
                    'question_id': qa_pair['question_id'],
                    'source_file': qa_pair.get('source_file', ''),
                    'entities': qa_pair.get('entities', []),
                    'context_length': qa_pair.get('context_length', 0),
                    'word_count': qa_pair.get('word_count', 0)
                }
            )
            documents.append(doc)
        
        return documents
    
    def initialize_qa_chain(self, search_mode: str = "balanced", model_type: str = "local", api_key: str = None):
        """Инициализация QA цепи"""
        search_config = get_model_config(search_mode)
        
        retriever = self.vector_store.as_retriever(
            search_type=search_config["search_type"],
            search_kwargs={k: v for k, v in search_config.items() if k != "search_type"}
        )
        
        # Выбор промта
        prompt_template = TransneftConfig.PROMPT_TEMPLATES["expert"]
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Выбор модели
        if model_type == "openai" and api_key:
            llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                openai_api_key=api_key,
                temperature=0.1,
                max_tokens=1000
            )
        else:
            # Локальная реализация
            from langchain.llms import FakeListLLM
            responses = [
                "На основе данных ПАО 'Транснефть'...",
                "Согласно корпоративной информации...",
                "В документации компании указано..."
            ]
            llm = FakeListLLM(responses=responses)
        
        # Создание QA цепи
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )
    
    def ask_question(self, question: str) -> Dict[str, Any]:
        """Задать вопрос системе"""
        if not self.qa_chain:
            raise ValueError("QA система не инициализирована")
        
        result = self.qa_chain({"query": question})
        return result
    
    def evaluate_system(self, sample_size: int = None) -> Dict[str, Any]:
        """Оценка системы на бенчмарке"""
        if not self.qa_chain:
            raise ValueError("QA система не инициализирована")
        
        # Выборка для оценки
        eval_qa_pairs = self.qa_pairs
        if sample_size and sample_size < len(self.qa_pairs):
            indices = np.random.choice(len(self.qa_pairs), sample_size, replace=False)
            eval_qa_pairs = [self.qa_pairs[i] for i in indices]
        
        generated_answers = []
        reference_answers = []
        questions = []
        sections = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, qa_pair in enumerate(eval_qa_pairs):
            status_text.text(f"Обработка {i+1}/{len(eval_qa_pairs)}: {qa_pair['question_id']}")
            
            try:
                result = self.ask_question(qa_pair['question'])
                generated_answers.append(result['result'])
                reference_answers.append(qa_pair['answer'])
                questions.append(qa_pair['question'])
                sections.append(qa_pair['section'])
                
                progress_bar.progress((i + 1) / len(eval_qa_pairs))
                
            except Exception as e:
                st.warning(f"Пропуск {qa_pair['question_id']}: {str(e)}")
                continue
        
        status_text.empty()
        
        # Расчет метрик
        metrics = self.calculate_metrics(generated_answers, reference_answers)
        
        return {
            'metrics': metrics,
            'generated_answers': generated_answers,
            'reference_answers': reference_answers,
            'questions': questions,
            'sections': sections,
            'eval_qa_pairs': eval_qa_pairs
        }
    
    def calculate_metrics(self, generated_answers: List[str], reference_answers: List[str]) -> Dict[str, float]:
        """Расчет метрик качества"""
        # ROUGE
        rouge_scorer_obj = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'], 
            use_stemmer=True
        )
        
        rouge_scores = []
        for gen, ref in zip(generated_answers, reference_answers):
            scores = rouge_scorer_obj.score(ref, gen)
            rouge_scores.append({
                'rouge1': scores['rouge1'].fmeasure,
                'rouge2': scores['rouge2'].fmeasure,
                'rougeL': scores['rougeL'].fmeasure
            })
        
        # BLEU
        bleu_scores = []
        for gen, ref in zip(generated_answers, reference_answers):
            reference = [ref.split()]
            candidate = gen.split()
            bleu_scores.append(sentence_bleu(reference, candidate))
        
        # BERTScore
        try:
            P, R, F1 = bert_score(generated_answers, reference_answers, lang="ru")
            bertscore_f1 = F1.mean().item()
        except:
            bertscore_f1 = 0.0
        
        # Метеор
        try:
            meteor = evaluate.load('meteor')
            meteor_score = meteor.compute(
                predictions=generated_answers, 
                references=reference_answers
            )['meteor']
        except:
            meteor_score = 0.0
        
        # Агрегация результатов
        rouge_df = pd.DataFrame(rouge_scores)
        
        return {
            'rouge1': rouge_df['rouge1'].mean(),
            'rouge2': rouge_df['rouge2'].mean(),
            'rougeL': rouge_df['rougeL'].mean(),
            'bleu': np.mean(bleu_scores),
            'bertscore': bertscore_f1,
            'meteor': meteor_score,
            'num_evaluated': len(generated_answers)
        }

def main():
    """Основная функция Streamlit приложения"""
    st.set_page_config(
        page_title="🤖 Транснефть QA Система",
        page_icon="🛢️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Стили
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-left: 4px solid #1e3c72;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Заголовок
    st.markdown("""
    <div class="main-header">
        <h1>🛢️ AI Чат-бот ПАО "Транснефть"</h1>
        <h3>Экспертная система на основе корпоративного бенчмарка</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Инициализация системы
    if 'qa_system' not in st.session_state:
        try:
            st.session_state.qa_system = TransneftBenchmarkQA()
            st.session_state.benchmark_analyzer = BenchmarkAnalyzer(TransneftConfig.BENCHMARK_PATH)
            
            with st.spinner("🚀 Инициализация системы..."):
                doc_count = st.session_state.qa_system.initialize_system()
                
            st.session_state.system_ready = True
            st.success(f"✅ Система готова! Обработано {doc_count} документов")
            
        except Exception as e:
            st.error(f"❌ Ошибка инициализации: {str(e)}")
            st.session_state.system_ready = False
    
    # Дальнейший код интерфейса...
    # [Остальная часть кода из предыдущего ответа]

if __name__ == "__main__":
    main()