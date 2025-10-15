import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    session_id: str
    user_id: str = "default"
    question: str = ""
    answer: str = ""
    sources: str = ""
    timestamp: datetime = None
    response_time: float = 0.0
    model_used: str = "transneft_qa"
    rating: int = 0
    feedback: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class EvaluationResult:
    evaluation_date: datetime
    sample_size: int
    rouge1: float
    rouge2: float
    rougeL: float
    bleu: float
    bertscore: float
    meteor: float
    overall_score: float
    duration_seconds: float

    def __post_init__(self):
        if self.evaluation_date is None:
            self.evaluation_date = datetime.now()


class DatabaseManager:

    def __init__(self, db_path: str = "data/transneft_qa.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        try:
            import os
            os.makedirs("data", exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        user_id TEXT DEFAULT 'default',
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        sources TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        response_time REAL DEFAULT 0,
                        model_used TEXT DEFAULT 'transneft_qa',
                        rating INTEGER DEFAULT 0,
                        feedback TEXT
                    )
                ''')

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluation_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        evaluation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        sample_size INTEGER,
                        rouge1 REAL,
                        rouge2 REAL,
                        rougeL REAL,
                        bleu REAL,
                        bertscore REAL,
                        meteor REAL,
                        overall_score REAL,
                        duration_seconds REAL
                    )
                ''')

                conn.commit()
                logger.info("База данных инициализирована успешно")

        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
            raise

    def save_chat_message(self, chat_message: ChatMessage) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO chat_messages 
                    (session_id, user_id, question, answer, sources, timestamp, response_time, model_used, rating, feedback)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chat_message.session_id,
                    chat_message.user_id,
                    chat_message.question,
                    chat_message.answer,
                    chat_message.sources,
                    chat_message.timestamp,
                    chat_message.response_time,
                    chat_message.model_used,
                    chat_message.rating,
                    chat_message.feedback
                ))

                conn.commit()
                return cursor.lastrowid

        except Exception as e:
            logger.error(f"Ошибка сохранения сообщения: {e}")
            return -1

    def save_evaluation_result(self, eval_result: EvaluationResult) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO evaluation_results 
                    (evaluation_date, sample_size, rouge1, rouge2, rougeL, bleu, bertscore, meteor, overall_score, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    eval_result.evaluation_date,
                    eval_result.sample_size,
                    eval_result.rouge1,
                    eval_result.rouge2,
                    eval_result.rougeL,
                    eval_result.bleu,
                    eval_result.bertscore,
                    eval_result.meteor,
                    eval_result.overall_score,
                    eval_result.duration_seconds
                ))

                conn.commit()
                return cursor.lastrowid

        except Exception as e:
            logger.error(f"Ошибка сохранения результата оценки: {e}")
            return -1

    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM chat_messages 
                    WHERE session_id = ? 
                    ORDER BY timestamp ASC 
                    LIMIT ?
                ''', (session_id, limit))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Ошибка получения истории чата: {e}")
            return []

    def get_evaluation_history(self, limit: int = 10) -> List[EvaluationResult]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT * FROM evaluation_results 
                    ORDER BY evaluation_date DESC 
                    LIMIT ?
                ''', (limit,))

                rows = cursor.fetchall()
                results = []

                for row in rows:
                    results.append(EvaluationResult(
                        evaluation_date=datetime.fromisoformat(row[1]) if isinstance(row[1], str) else row[1],
                        sample_size=row[2],
                        rouge1=row[3],
                        rouge2=row[4],
                        rougeL=row[5],
                        bleu=row[6],
                        bertscore=row[7],
                        meteor=row[8],
                        overall_score=row[9],
                        duration_seconds=row[10]
                    ))

                return results

        except Exception as e:
            logger.error(f"Ошибка получения истории оценок: {e}")
            return []

    def get_chat_statistics(self, user_id: str = None) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Общая статистика
                query = "SELECT COUNT(*) FROM chat_messages"
                params = ()

                if user_id:
                    query += " WHERE user_id = ?"
                    params = (user_id,)

                cursor.execute(query, params)
                total_messages = cursor.fetchone()[0]
                query = "SELECT COUNT(*) FROM chat_messages WHERE rating > 0"
                if user_id:
                    query += " AND user_id = ?"
                    params = (user_id,)

                cursor.execute(query, params)
                rated_messages = cursor.fetchone()[0]
                query = "SELECT AVG(rating) FROM chat_messages WHERE rating > 0"
                if user_id:
                    query += " AND user_id = ?"
                    params = (user_id,)

                cursor.execute(query, params)
                avg_rating_result = cursor.fetchone()[0]
                avg_rating = float(avg_rating_result) if avg_rating_result else 0.0

                query = "SELECT AVG(response_time) FROM chat_messages WHERE response_time > 0"
                if user_id:
                    query += " AND user_id = ?"

                cursor.execute(query, params)
                avg_response_time_result = cursor.fetchone()[0]
                avg_response_time = float(avg_response_time_result) if avg_response_time_result else 0.0

                return {
                    'total_messages': total_messages,
                    'rated_messages': rated_messages,
                    'avg_rating': avg_rating,
                    'avg_response_time': avg_response_time
                }

        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {
                'total_messages': 0,
                'rated_messages': 0,
                'avg_rating': 0,
                'avg_response_time': 0
            }

    def get_user_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT 
                        session_id,
                        MIN(timestamp) as start_time,
                        MAX(timestamp) as end_time,
                        COUNT(*) as message_count
                    FROM chat_messages 
                    WHERE user_id = ?
                    GROUP BY session_id
                    ORDER BY start_time DESC
                    LIMIT ?
                ''', (user_id, limit))

                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Ошибка получения сессий: {e}")
            return []

    def add_feedback(self, message_id: int, rating: int, feedback: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE chat_messages 
                    SET rating = ?, feedback = ?
                    WHERE id = ?
                ''', (rating, feedback, message_id))

                conn.commit()
                return True

        except Exception as e:
            logger.error(f"Ошибка добавления отзыва: {e}")
            return False

    def export_chat_history(self, session_id: str = None, format_type: str = "json") -> str:
        try:
            if session_id:
                messages = self.get_chat_history(session_id, limit=1000)
            else:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM chat_messages ORDER BY timestamp')
                    messages = [dict(row) for row in cursor.fetchall()]

            if format_type == "json":
                return json.dumps(messages, ensure_ascii=False, indent=2, default=str)
            else:  # csv
                import pandas as pd
                df = pd.DataFrame(messages)
                return df.to_csv(index=False, encoding='utf-8')

        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")
            return ""

db_manager = DatabaseManager()