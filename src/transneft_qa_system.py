import os
import warnings
import streamlit as st
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any
from datetime import datetime
import uuid
import time
import sys

sys.path.append('src')

from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu
import evaluate
from bert_score import score as bert_score

from config import TransneftConfig, EvaluationCriteria
from benchmark_utils import BenchmarkAnalyzer, export_benchmark_report
from ui_components import StyleUI, AvatarManager, DatabaseUI
from database_models import DatabaseManager, ChatMessage, EvaluationResult, db_manager
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction  

os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
warnings.filterwarnings("ignore", category=UserWarning, module="nltk")
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

def calculate_bleu(reference, candidate):
    smoothie = SmoothingFunction().method4
    return sentence_bleu([reference], candidate, smoothing_function=smoothie)

class SimpleRAGSystem:
    def __init__(self, vector_store_path: str = "models/vector_store"):
        st.info("Инициализация RAG системы...")
        try:
            from src.data_processing.vector_store import VectorStore
            self.vector_store = VectorStore()
            with open("src/data_processing/data/processed/document_chunks.json", "r", encoding="utf-8") as f:
                chunks = json.load(f)
            self.vector_store.create_embeddings(chunks)
            self.vector_store.save_index()
            st.success("✅ RAG система готова")
        except Exception as e:
            st.error(f"❌ Ошибка инициализации RAG системы: {str(e)}")
            raise

    def answer_question(self, question: str, k_retrieval: int = 3) -> Dict:
        retrieved_docs = self.vector_store.search(question, k=k_retrieval)

        if not retrieved_docs:
            return {
                "answer": "Не найдено релевантной информации в базе знаний.",
                "sources": [],
                "confidence": 0.0
            }

        answer = self._extract_best_answer(question, retrieved_docs)
        sources = []
        total_confidence = 0.0

        for doc_text, metadata, score in retrieved_docs:
            sources.append({
                "content": doc_text[:200] + "...",
                "sections": metadata.get('sections', []),
                "score": score,
                "chunk_id": metadata.get('chunk_id')
            })
            total_confidence += score

        avg_confidence = total_confidence / len(retrieved_docs) if retrieved_docs else 0.0

        return {
            "answer": answer,
            "sources": sources,
            "confidence": avg_confidence,
            "retrieved_docs_count": len(retrieved_docs)
        }

    def _extract_best_answer(self, question: str, retrieved_docs: List) -> str:
        question_words = set(question.lower().split())
        best_answer = ""
        best_score = 0

        for doc_text, metadata, score in retrieved_docs:
            sentences = [s.strip() for s in doc_text.split('.') if s.strip()]
            for sentence in sentences:
                if len(sentence) < 20:
                    continue
                sentence_words = set(sentence.lower().split())
                common_words = question_words.intersection(sentence_words)
                relevance_score = len(common_words)
                if relevance_score > best_score:
                    best_score = relevance_score
                    best_answer = sentence

        if best_answer:
            return f"На основе предоставленной информации: {best_answer.strip()}."
        else:
            most_relevant_doc = retrieved_docs[0][0]
            return f"Наиболее релевантная информация: {most_relevant_doc[:300]}..."

class TransneftBenchmarkQA:
    def __init__(self, benchmark_path: str = None):
        self.benchmark_path = benchmark_path or TransneftConfig.BENCHMARK_PATH
        self.benchmark_data = None
        self.rag_system = None
        self.qa_pairs = []
        self.sections = []
        self.db_manager = db_manager
        self.load_benchmark()

    def load_benchmark(self):
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

    def initialize_system(self):
        if not self.benchmark_data:
            raise ValueError("Бенчмарк не загружен")

        try:
            self.rag_system = SimpleRAGSystem()
            st.success("✅ RAG система инициализирована")
            return 1
        except Exception as e:
            st.error(f"❌ Ошибка инициализации системы: {str(e)}")
            return 0


def ask_question(self, question: str, session_id: str, user_id: str = "default") -> Dict[str, Any]:
    # ПРОВЕРЯЕМ что RAG система инициализирована
    if self.rag_system is None:
        print("❌ RAG system is not initialized!")
        return {
            'result': "Система временно недоступна. Идет инициализация...",
            'source_documents': [],
            'confidence': 0.0
        }
    
    start_time = time.time()

    try:
        # Теперь безопасно используем rag_system
        result = self.rag_system.answer_question(question)
        response_time = time.time() - start_time

        chat_message = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            question=question,
            answer=result['answer'],
            sources=json.dumps(result['sources'], ensure_ascii=False),
            timestamp=datetime.now(),
            response_time=response_time,
            model_used="simple_rag_system"
        )

        message_id = self.db_manager.save_chat_message(chat_message)
        
        return {
            'result': result['answer'],
            'source_documents': result['sources'],
            'message_id': message_id,
            'confidence': result['confidence']
        }

    except Exception as e:
        # Обработка других ошибок
        response_time = time.time() - start_time
        error_message = ChatMessage(
            session_id=session_id,
            user_id=user_id,
            question=question,
            answer=f"Ошибка: {str(e)}",
            timestamp=datetime.now(),
            response_time=response_time,
            model_used="error"
        )
        self.db_manager.save_chat_message(error_message)
        raise e
    '''def ask_question(self, question: str, session_id: str, user_id: str = "default") -> Dict[str, Any]:
        start_time = time.time()

        try:
            result = self.rag_system.answer_question(question)
            response_time = time.time() - start_time

            chat_message = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                question=question,
                answer=result['answer'],
                sources=json.dumps(result['sources'], ensure_ascii=False),
                timestamp=datetime.now(),
                response_time=response_time,
                model_used="simple_rag_system"
            )

            message_id = self.db_manager.save_chat_message(chat_message)
            
            return {
                'result': result['answer'],
                'source_documents': result['sources'],
                'message_id': message_id,
                'confidence': result['confidence']
            }

        except Exception as e:
            response_time = time.time() - start_time
            error_message = ChatMessage(
                session_id=session_id,
                user_id=user_id,
                question=question,
                answer=f"Ошибка: {str(e)}",
                timestamp=datetime.now(),
                response_time=response_time,
                model_used="error"
            )
            self.db_manager.save_chat_message(error_message)
            raise e
'''
    def evaluate_system(self, sample_size: int = None) -> Dict[str, Any]:
        if not self.rag_system:
            raise ValueError("RAG система не инициализирована")

        start_time = time.time()
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
            status_text.text(f"Обработка {i + 1}/{len(eval_qa_pairs)}: {qa_pair['question_id']}")
            try:
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
        metrics = self.calculate_metrics(generated_answers, reference_answers)
        duration = time.time() - start_time

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

        bleu_scores = []
        for gen, ref in zip(generated_answers, reference_answers):
            reference = [ref.split()]
            candidate = gen.split()
            bleu_scores.append(sentence_bleu(reference, candidate))

        try:
            P, R, F1 = bert_score(generated_answers, reference_answers, lang="ru")
            bertscore_f1 = F1.mean().item()
        except:
            bertscore_f1 = 0.0

        try:
            meteor = evaluate.load('meteor')
            meteor_score = meteor.compute(
                predictions=generated_answers,
                references=reference_answers
            )['meteor']
        except:
            meteor_score = 0.0

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
        messages = self.db_manager.get_chat_history(session_id)
        chat_history = []
        for msg in messages:
            try:
                sources = json.loads(msg.sources) if msg.sources else []
            except:
                sources = []

            try:
                if hasattr(msg['timestamp'], 'strftime'):
                    timestamp_str = msg['timestamp'].strftime("%H:%M:%S")
                else:
                    timestamp_str = str( msg['timestamp']) if  msg['timestamp'] else ""
            except:
                timestamp_str = ""

            chat_history.append((
                msg['question'] if msg['question'] else "",
                msg['answer'] if msg['answer'] else "",
                sources,
                timestamp_str
            ))
        return chat_history

def main():
    st.set_page_config(
        page_title=TransneftConfig.UI_CONFIG["page_title"],
        page_icon=TransneftConfig.UI_CONFIG["page_icon"],
        layout=TransneftConfig.UI_CONFIG["layout"],
        initial_sidebar_state=TransneftConfig.UI_CONFIG["initial_sidebar_state"]
    )

    StyleUI.load_css()

    if 'current_session' not in st.session_state:
        st.session_state.current_session = str(uuid.uuid4())

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "Чат-бот"

    StyleUI.create_header("Алексей Петров")

    with st.sidebar:
        StyleUI.create_sidebar_navigation()

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

        StyleUI.upload_avatar()

        st.markdown("---")
        st.subheader("⚙️ Настройки системы")

        st.markdown("---")
        st.subheader("💾 Управление историей")
        DatabaseUI.display_chat_history_controls()

        st.markdown("---")
        st.subheader("ℹ️ О системе")
        st.info("""
        Экспертная система вопросов и ответов 
        на основе данных ПАО "Транснефть".
        
        Использует RAG-архитектуру и современные
        языковые модели.
        """)

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
    if 'qa_system' not in st.session_state:
        with st.spinner("🔄 Инициализация системы..."):
            try:
                st.session_state.qa_system = TransneftBenchmarkQA()
                doc_count = st.session_state.qa_system.initialize_system()
                st.session_state.system_ready = True
                st.success("✅ Система готова!")

                st.session_state.chat_history = st.session_state.qa_system.load_chat_history(
                    st.session_state.current_session
                )

            except Exception as e:
                st.error(f"❌ Ошибка инициализации: {str(e)}")
                st.session_state.system_ready = False

    StyleUI.create_search_section()
    StyleUI.create_quick_actions()

    st.markdown("### 💭 История диалога")

    if not st.session_state.chat_history:
        st.info("💡 Задайте первый вопрос о ПАО 'Транснефть'")
    else:
        for i, (question, answer, sources, timestamp) in enumerate(st.session_state.chat_history):
            StyleUI.display_chat_message(question, is_user=True, timestamp=timestamp)
            StyleUI.display_chat_message(answer, is_user=False, timestamp=timestamp)

            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("⭐ Оценить", key=f"rate_{i}", use_container_width=True):
                    st.session_state.rate_message_idx = i

            if sources:
                with st.expander("📚 Показать источники"):
                    StyleUI.display_source_documents(sources)

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

                        st.session_state.chat_history = st.session_state.qa_system.load_chat_history(
                            st.session_state.current_session
                        )

                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Ошибка при обработке вопроса: {str(e)}")

def display_history_interface():
    st.markdown("## 📊 История сессий")

    if 'qa_system' not in st.session_state:
        st.warning("⚠️ Сначала инициализируйте систему")
        return

    stats = db_manager.get_chat_statistics("user")
    DatabaseUI.display_session_analytics(stats)

    st.markdown("---")
    DatabaseUI.display_export_options()

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

            StyleUI.display_metric_card(
                "ROUGE-1",
                f"{metrics['rouge1']:.3f}",
                help_text="Схожесть униграмм"
            )

            StyleUI.display_metric_card(
                "ROUGE-2",
                f"{metrics['rouge2']:.3f}",
                help_text="Схожесть биграмм"
            )

            StyleUI.display_metric_card(
                "BERTScore",
                f"{metrics['bertscore']:.3f}",
                help_text="Семантическая схожесть"
            )

            overall_score = EvaluationCriteria.calculate_overall_score(metrics)
            quality_level = EvaluationCriteria.get_quality_level(overall_score, "overall")

            st.markdown(f"""
            <div class="metric-card">
                <h4 style="margin: 0 0 0.5rem 0; color: #333;">Общая оценка</h4>
                <h2 style="margin: 0; color: #1e6cde;">{overall_score:.3f}</h2>
                <p style="margin: 0; color: #666;">Уровень: {quality_level}</p>
            </div>
            """, unsafe_allow_html=True)

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
    st.markdown("## 📊 Аналитика системы")

    if 'qa_system' not in st.session_state:
        st.warning("⚠️ Сначала инициализируйте систему")
        return

    analyzer = BenchmarkAnalyzer()

    if not analyzer.data:
        st.error("❌ Не удалось загрузить бенчмарк для анализа")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 Статистика бенчмарка")
        stats = analyzer.get_basic_stats()

        StyleUI.display_metric_card(
            "Всего QA пар",
            stats.get('total_qa_pairs', 0)
        )

        StyleUI.display_metric_card(
            "Уникальные секции",
            stats.get('unique_qa_sections', 0)
        )

        StyleUI.display_metric_card(
            "Средняя длина контекста",
            f"{stats.get('avg_context_length', 0):.0f} симв."
        )

    with col2:
        st.markdown("### 🔍 Визуализация")

        try:
            figures = analyzer.visualize_benchmark()
            displayed_figures = 0
            
            for fig in figures:
                if fig is not None and hasattr(fig, 'update_layout'):
                    st.plotly_chart(fig, use_container_width=True)
                    displayed_figures += 1
                    if displayed_figures >= 2:
                        break
            
            if displayed_figures == 0:
                st.info("""
                **ℹ️ Информация о визуализации:**
                
                Для отображения графиков необходимо:
                - Не менее 3 QA пар в бенчмарке
                - Данные с различными секциями
                - Контексты разной длины
                """)
                
        except Exception as e:
            st.warning(f"⚠️ Ошибка при создании визуализации: {str(e)}")

def display_admin_interface():
    st.markdown("## 🔧 Администрирование системы")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💾 База данных")

        db_stats = db_manager.get_chat_statistics()
        st.metric("Всего сообщений", db_stats['total_messages'])
        st.metric("Оцененных сообщений", db_stats['rated_messages'])
        st.metric("Средняя оценка",
                  f"{db_stats['avg_rating']:.1f}⭐" if db_stats['avg_rating'] > 0 else "Нет оценок")

        st.markdown("### 🛠️ Управление")

        if st.button("🔄 Очистить кэш", use_container_width=True):
            st.info("Функция очистки кэша в разработке")

        if st.button("📋 Создать бэкап", use_container_width=True):
            st.info("Функция бэкапа в разработке")

    with col2:
        st.markdown("### 📊 Системная информация")

        st.metric("Версия Python", sys.version.split()[0])
        st.metric("Память БД", f"{os.path.getsize('data/chat_history.db') / 1024 / 1024:.1f} МБ")

        st.markdown("### 📝 Последние действия")
        st.info("""
        - Система инициализирована
        - База данных подключена
        - Готов к работе
        """)

if __name__ == "__main__":
    main()