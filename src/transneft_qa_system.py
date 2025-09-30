"""
Главный файл системы Транснефть QA с интеграцией базы данных
"""

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
import uuid
import time

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
from config import TransneftConfig, get_model_config, validate_benchmark_path, EvaluationCriteria
from benchmark_utils import BenchmarkAnalyzer, export_benchmark_report
from ui_components import GosuslugiUI, AvatarManager, DatabaseUI
from database_models import DatabaseManager, ChatMessage, EvaluationResult, db_manager


class TransneftBenchmarkQA:
    """Основной класс QA системы для Транснефть с интеграцией БД"""
    
    def __init__(self, benchmark_path: str = None):
        self.benchmark_path = benchmark_path or TransneftConfig.BENCHMARK_PATH
        self.benchmark_data = None
        self.vector_store = None
        self.qa_chain = None
        self.embeddings = None
        self.qa_pairs = []
        self.sections = []
        self.db_manager = db_manager
        
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
    
    def ask_question(self, question: str, session_id: str, user_id: str = "default") -> Dict[str, Any]:
        """Задать вопрос системе с сохранением в БД"""
        if not self.qa_chain:
            raise ValueError("QA система не инициализирована")
        
        start_time = time.time()
        
        try:
            result = self.qa_chain({"query": question})
            response_time = time.time() - start_time
            
            # Сохраняем в базу данных
            chat_message = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                question=question,
                answer=result['result'],
                sources=json.dumps([
                    {
                        'content': doc.page_content[:500],
                        'section': doc.metadata.get('section', ''),
                        'source': doc.metadata.get('source_file', '')
                    }
                    for doc in result.get('source_documents', [])
                ], ensure_ascii=False),
                timestamp=datetime.now(),
                response_time=response_time,
                model_used="transneft_qa"
            )
            
            message_id = self.db_manager.save_chat_message(chat_message)
            result['message_id'] = message_id
            
            return result
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # Сохраняем ошибку в базу данных
            error_message = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                question=question,
                answer=f"Ошибка: {str(e)}",
                timestamp=datetime.now(),
                response_time=response_time,
                model_used="transneft_qa_error"
            )
            
            self.db_manager.save_chat_message(error_message)
            raise e
    
    def evaluate_system(self, sample_size: int = None) -> Dict[str, Any]:
        """Оценка системы на бенчмарке с сохранением в БД"""
        if not self.qa_chain:
            raise ValueError("QA система не инициализирована")
        
        start_time = time.time()
        
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
                # Используем временную сессию для оценки
                result = self.ask_question(qa_pair['question'], "evaluation_session", "system")
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
        duration = time.time() - start_time
        
        # Сохранение результатов оценки
        eval_result = EvaluationResult(
            evaluation_date=datetime.now(),
            sample_size=len(generated_answers),
            rouge1=metrics['rouge1'],
            rouge2=metrics['rouge2'],
            rougeL=metrics['rougeL'],
            bleu=metrics['bleu'],
            bertscore=metrics['bertscore'],
            meteor=metrics['meteor'],
            overall_score=EvaluationCriteria.calculate_overall_score(metrics),
            duration_seconds=duration
        )
        
        eval_id = self.db_manager.save_evaluation_result(eval_result)
        metrics['evaluation_id'] = eval_id
        
        return {
            'metrics': metrics,
            'generated_answers': generated_answers,
            'reference_answers': reference_answers,
            'questions': questions,
            'sections': sections,
            'eval_qa_pairs': eval_qa_pairs,
            'evaluation_result': eval_result
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
    
    def load_chat_history(self, session_id: str) -> List[Tuple[str, str, list, str]]:
        """Загрузка истории чата из базы данных"""
        messages = self.db_manager.get_chat_history(session_id)
        
        chat_history = []
        for msg in messages:
            try:
                sources = json.loads(msg.sources) if msg.sources else []
            except:
                sources = []
            
            chat_history.append((
                msg.question,
                msg.answer,
                sources,
                msg.timestamp.strftime("%H:%M:%S") if msg.timestamp else ""
            ))
        
        return chat_history


def main():
    """Основная функция Streamlit приложения"""
    
    # Конфигурация страницы
    st.set_page_config(
        page_title=TransneftConfig.UI_CONFIG["page_title"],
        page_icon=TransneftConfig.UI_CONFIG["page_icon"],
        layout=TransneftConfig.UI_CONFIG["layout"],
        initial_sidebar_state=TransneftConfig.UI_CONFIG["initial_sidebar_state"]
    )
    
    # Загрузка CSS стилей
    GosuslugiUI.load_css()
    
    # Инициализация сессии
    if 'current_session' not in st.session_state:
        st.session_state.current_session = str(uuid.uuid4())
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "Чат-бот"
    
    # Создание шапки
    GosuslugiUI.create_header("Алексей Петров")
    
    # Сайдбар с навигацией
    with st.sidebar:
        GosuslugiUI.create_sidebar_navigation()
        
        # Информация о сессии
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0 0 0.5rem 0; color: #333;">Текущая сессия</h4>
            <p style="margin: 0; font-size: 0.8rem; color: #666;">
                ID: {st.session_state.current_session[:8]}...
            </p>
            <p style="margin: 0; font-size: 0.8rem; color: #666;">
                Сообщений: {len(st.session_state.chat_history)}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Загрузка аватара
        GosuslugiUI.upload_avatar()
        
        # Настройки системы
        st.markdown("---")
        st.subheader("⚙️ Настройки системы")
        
        # Выбор модели поиска
        search_mode = st.selectbox(
            "Режим поиска:",
            ["balanced", "precision", "recall"],
            format_func=lambda x: {
                "balanced": "⚖️ Сбалансированный",
                "precision": "🎯 Точность", 
                "recall": "🔍 Полнота"
            }[x]
        )
        
        # Настройки API
        use_openai = st.checkbox("Использовать OpenAI GPT")
        api_key = None
        if use_openai:
            api_key = st.text_input("OpenAI API Key:", type="password")
        
        # Управление историей
        st.markdown("---")
        st.subheader("💾 Управление историей")
        DatabaseUI.display_chat_history_controls()
        
        # Информация о системе
        st.markdown("---")
        st.subheader("ℹ️ О системе")
        st.info("""
        Экспертная система вопросов и ответов 
        на основе данных ПАО "Транснефть".
        
        Использует RAG-архитектуру и современные
        языковые модели.
        """)
    
    # Основные вкладки
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Чат-бот", "📊 История", "🧪 Оценка качества", "📈 Аналитика", "🔧 Администрирование"
    ])
    
    with tab1:
        display_chat_interface()
    
    with tab2:
        display_history_interface()
    
    with tab3:
        display_evaluation_interface()
    
    with tab4:
        display_analytics_interface()
    
    with tab5:
        display_admin_interface()


def display_chat_interface():
    """Отображение интерфейса чат-бота"""
    
    # Инициализация системы
    if 'qa_system' not in st.session_state:
        with st.spinner("🔄 Инициализация системы..."):
            try:
                st.session_state.qa_system = TransneftBenchmarkQA()
                doc_count = st.session_state.qa_system.initialize_system()
                st.session_state.system_ready = True
                st.success(f"✅ Система готова! Обработано {doc_count} документов")
                
                # Загрузка истории из БД
                st.session_state.chat_history = st.session_state.qa_system.load_chat_history(
                    st.session_state.current_session
                )
                
            except Exception as e:
                st.error(f"❌ Ошибка инициализации: {str(e)}")
                st.session_state.system_ready = False
    
    # Секция поиска
    GosuslugiUI.create_search_section()
    
    # Быстрые действия
    GosuslugiUI.create_quick_actions()
    
    # История чата
    st.markdown("### 💭 История диалога")
    
    if not st.session_state.chat_history:
        st.info("💡 Задайте первый вопрос о ПАО 'Транснефть'")
    else:
        for i, (question, answer, sources, timestamp) in enumerate(st.session_state.chat_history):
            GosuslugiUI.display_chat_message(question, is_user=True, timestamp=timestamp)
            GosuslugiUI.display_chat_message(answer, is_user=False, timestamp=timestamp)
            
            # Кнопка оценки ответа
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("⭐ Оценить", key=f"rate_{i}", use_container_width=True):
                    st.session_state.rate_message_idx = i
            
            if sources:
                with st.expander("📚 Показать источники"):
                    GosuslugiUI.display_source_documents(sources)
    
    # Форма для нового вопроса
    st.markdown("---")
    st.markdown("### 💬 Новый вопрос")
    
    with st.form("question_form", clear_on_submit=True):
        question = st.text_area(
            "Ваш вопрос:",
            placeholder="Например: Каков размер уставного капитала Транснефти? Или: Когда компания была основана?",
            height=100
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submitted = st.form_submit_button("🚀 Отправить вопрос", use_container_width=True)
        
        with col2:
            show_sources = st.checkbox("Показать источники", value=True)
        
        if submitted and question:
            if not st.session_state.get('system_ready', False):
                st.error("❌ Система не готова. Подождите завершения инициализации.")
            else:
                with st.spinner("🔍 Ищем ответ в базе знаний..."):
                    try:
                        result = st.session_state.qa_system.ask_question(
                            question, 
                            st.session_state.current_session,
                            "user"
                        )
                        
                        # Обновляем историю из БД
                        st.session_state.chat_history = st.session_state.qa_system.load_chat_history(
                            st.session_state.current_session
                        )
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Ошибка при обработке вопроса: {str(e)}")


def display_history_interface():
    """Отображение интерфейса истории"""
    
    st.markdown("## 📊 История сессий")
    
    if 'qa_system' not in st.session_state:
        st.warning("⚠️ Сначала инициализируйте систему")
        return
    
    # Статистика пользователя
    stats = db_manager.get_chat_statistics("user")
    DatabaseUI.display_session_analytics(stats)
    
    # Экспорт данных
    st.markdown("---")
    DatabaseUI.display_export_options()
    
    # История сессий
    st.markdown("---")
    st.markdown("### 📋 Предыдущие сессии")
    
    sessions = db_manager.get_user_sessions("user", limit=10)
    
    if not sessions:
        st.info("ℹ️ Нет сохраненных сессий")
    else:
        for session in sessions:
            with st.expander(f"Сессия {session['session_id'][:8]}... ({session['start_time']})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Сообщений", session['message_count'])
                
                with col2:
                    st.metric("Начало", session['start_time'][:16])
                
                with col3:
                    if st.button("🔄 Загрузить", key=f"load_{session['session_id']}"):
                        st.session_state.current_session = session['session_id']
                        st.session_state.chat_history = st.session_state.qa_system.load_chat_history(
                            session['session_id']
                        )
                        st.session_state.current_tab = "Чат-бот"
                        st.rerun()


def display_evaluation_interface():
    """Отображение интерфейса оценки качества"""
    
    st.markdown("## 🧪 Оценка качества системы")
    
    if 'qa_system' not in st.session_state or not st.session_state.get('system_ready', False):
        st.warning("⚠️ Сначала инициализируйте систему во вкладке 'Чат-бот'")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📊 Запуск оценки")
        
        sample_size = st.slider(
            "Размер выборки для оценки:",
            min_value=10,
            max_value=min(100, len(st.session_state.qa_system.qa_pairs)),
            value=30,
            step=5,
            help="Количество QA пар для тестирования"
        )
        
        if st.button("🎯 Запустить оценку", type="primary", use_container_width=True):
            with st.spinner("Провожу комплексную оценку системы..."):
                evaluation_results = st.session_state.qa_system.evaluate_system(sample_size)
                st.session_state.evaluation_results = evaluation_results
                st.success("✅ Оценка завершена!")
    
    with col2:
        st.markdown("### 📈 Метрики качества")
        
        if 'evaluation_results' in st.session_state:
            metrics = st.session_state.evaluation_results['metrics']
            
            # Отображение метрик в карточках
            GosuslugiUI.display_metric_card(
                "ROUGE-1", 
                f"{metrics['rouge1']:.3f}",
                help_text="Схожесть униграмм"
            )
            
            GosuslugiUI.display_metric_card(
                "ROUGE-2", 
                f"{metrics['rouge2']:.3f}",
                help_text="Схожесть биграмм"
            )
            
            GosuslugiUI.display_metric_card(
                "BERTScore", 
                f"{metrics['bertscore']:.3f}",
                help_text="Семантическая схожесть"
            )
            
            # Общая оценка
            overall_score = EvaluationCriteria.calculate_overall_score(metrics)
            quality_level = EvaluationCriteria.get_quality_level(overall_score, "overall")
            
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="margin: 0 0 0.5rem 0; color: #333;">Общая оценка</h4>
                <h2 style="margin: 0; color: #1e6cde;">{overall_score:.3f}</h2>
                <p style="margin: 0; color: #666;">Уровень: {quality_level}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # История оценок
        st.markdown("### 📅 История оценок")
        eval_history = db_manager.get_evaluation_history(limit=5)
        
        for eval_result in eval_history:
            with st.expander(f"Оценка от {eval_result.evaluation_date.strftime('%d.%m.%Y %H:%M')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Выборка", eval_result.sample_size)
                    st.metric("ROUGE-1", f"{eval_result.rouge1:.3f}")
                with col2:
                    st.metric("Общий балл", f"{eval_result.overall_score:.3f}")
                    st.metric("Длительность", f"{eval_result.duration_seconds:.1f}с")


def display_analytics_interface():
    """Отображение аналитики системы"""
    
    st.markdown("## 📊 Аналитика системы")
    
    if 'qa_system' not in st.session_state:
        st.warning("⚠️ Сначала инициализируйте систему")
        return
    
    # Анализ бенчмарка
    analyzer = BenchmarkAnalyzer()
    
    if not analyzer.data:
        st.error("❌ Не удалось загрузить бенчмарк для анализа")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Статистика бенчмарка")
        stats = analyzer.get_basic_stats()
        
        GosuslugiUI.display_metric_card(
            "Всего QA пар", 
            stats['total_qa_pairs']
        )
        
        GosuslugiUI.display_metric_card(
            "Уникальные секции", 
            stats['unique_qa_sections']
        )
        
        GosuslugiUI.display_metric_card(
            "Средняя длина контекста", 
            f"{stats['avg_context_length']:.0f} симв."
        )
    
    with col2:
        st.markdown("### 🔍 Визуализация")
        
        # Визуализации
        fig1, fig2, fig3 = analyzer.visualize_benchmark()
        
        if fig1:
            st.plotly_chart(fig1, use_container_width=True)
        
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)


def display_admin_interface():
    """Отображение интерфейса администрирования"""
    
    st.markdown("## 🔧 Администрирование системы")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💾 База данных")
        
        # Статистика БД
        db_stats = db_manager.get_chat_statistics()
        st.metric("Всего сообщений", db_stats['total_messages'])
        st.metric("Оцененных сообщений", db_stats['rated_messages'])
        st.metric("Средняя оценка", 
                 f"{db_stats['avg_rating']:.1f}⭐" if db_stats['avg_rating'] > 0 else "Нет оценок")
        
        # Управление БД
        st.markdown("### 🛠️ Управление")
        
        if st.button("🔄 Очистить кэш", use_container_width=True):
            st.info("Функция очистки кэша в разработке")
        
        if st.button("📋 Создать бэкап", use_container_width=True):
            st.info("Функция бэкапа в разработке")
    
    with col2:
        st.markdown("### 📊 Системная информация")
        
        # Информация о системе
        st.metric("Версия Python", sys.version.split()[0])
        st.metric("Память БД", f"{os.path.getsize('data/chat_history.db') / 1024 / 1024:.1f} МБ")
        
        # Логи
        st.markdown("### 📝 Последние действия")
        st.info("""
        - Система инициализирована
        - База данных подключена
        - Готов к работе
        """)


if __name__ == "__main__":
    main()