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

from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu
import evaluate
from bert_score import score as bert_score

from config import TransneftConfig, EvaluationCriteria 
from benchmark_utils import BenchmarkAnalyzer, export_benchmark_report
from ui_components import StyleUI, AvatarManager, DatabaseUI
from database_models import DatabaseManager, ChatMessage, EvaluationResult, db_manager
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction  
#from data_processing.simple_rag_system import SimpleRAGSystem

os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
warnings.filterwarnings("ignore", category=UserWarning, module="nltk")
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

def calculate_bleu(reference, candidate):
    smoothie = SmoothingFunction().method4
    return sentence_bleu([reference], candidate, smoothing_function=smoothie)
    

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
        self.load_benchmark()
        if not self.benchmark_data:
            raise ValueError("Бенчмарк не загружен")
        try:
            self.rag_system = TransneftBenchmarkQA()
            st.success("✅ RAG система инициализирована")
            return 1
        except Exception as e:
            st.error(f"❌ Ошибка инициализации системы: {str(e)}")
            return 0

    def answer_question(self, question: str):
        #ans = self.rag_system.answer_question(question)
        ans = {
    "result": "Текст ответа на вопрос",  # строка с ответом
    "source_documents": [  # список источников
        {
            "source": "название_источника_1",
            "content": "текст из источника",
            "relevance": 0.85,
            "metadata": {}  # опционально
        },
        {
            "source": "название_источника_2", 
            "content": "текст из источника",
            "relevance": 0.78,
            "metadata": {}
        }
    ],
    "message_id": 123,  # ID сообщения из БД (целое число)
    "confidence": 0.82  # уверенность ответа (float от 0.0 до 1.0)
}
        return ans
    def ask_question(self, question: str, session_id: str, user_id: str = "default") -> Dict[str, Any]:
        """Безопасный метод для вопросов с защитой от None"""
        print(f"🎯 Ask question called: {question}")
        print(f"🔍 RAG system state: {self.rag_system is not None}")
        
        # ЗАЩИТА ОТ None
        if self.rag_system is None:
            error_msg = "❌ RAG система не инициализирована!"
            print(error_msg)
            return {
                'result': "Система временно недоступна. Попробуйте инициализировать систему заново.",
                'source_documents': [],
                'confidence': 0.0,
                'message_id': -1
            }
        
        start_time = time.time()

        try:
            # Проверяем что метод существует
            if not hasattr(self.rag_system, 'answer_question'):
                return {
                    'result': "Ошибка: метод answer_question не найден",
                    'source_documents': [],
                    'confidence': 0.0,
                    'message_id': -1
                }
                
            result = self.rag_system.answer_question(question)
            response_time = time.time() - start_time

            # Сохраняем в базу (если доступно)
            message_id = -1
            try:
                chat_message = ChatMessage(
                    session_id=session_id,
                    user_id=user_id,
                    question=question,
                    answer=result['answer'],
                    sources=json.dumps(result.get('sources', []), ensure_ascii=False),
                    timestamp=datetime.now(),
                    response_time=response_time,
                    model_used="simple_rag_system"
                )
                message_id = self.db_manager.save_chat_message(chat_message)
            except Exception as db_error:
                print(f"⚠️ Ошибка сохранения в БД: {db_error}")

            return {
                'result': result.get('answer', 'Ответ не сгенерирован'),
                'source_documents': result.get('sources', []),
                'message_id': message_id,
                'confidence': result.get('confidence', 0.0)
            }

        except Exception as e:
            print(f"❌ Ошибка в answer_question: {e}")
            return {
                'result': f"⚠️ Ошибка обработки вопроса: {str(e)}",
                'source_documents': [],
                'confidence': 0.0,
                'message_id': -1
            }
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
    rag_system = TransneftBenchmarkQA()
    print(rag_system.benchmark_path)

if __name__ == "__main__":
    main()