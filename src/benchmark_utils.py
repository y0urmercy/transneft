"""
Утилиты для анализа бенчмарка
"""


import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Tuple, Optional
import json
from config import TransneftConfig


class BenchmarkAnalyzer:
    def __init__(self, benchmark_path: str = TransneftConfig.BENCHMARK_PATH):
        self.benchmark_path = benchmark_path
        self.data = self._load_benchmark()

    def _load_benchmark(self) -> Dict:
        try:
            import os
            if os.path.exists(self.benchmark_path):
                with open(self.benchmark_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Ошибка загрузки бенчмарка: {e}")
            return {}

    def get_basic_stats(self) -> Dict[str, any]:
        if not self.data:
            return {
                'total_qa_pairs': 0,
                'unique_qa_sections': 0,
                'avg_context_length': 0,
                'total_sections': 0
            }

        qa_pairs = self.data.get('qa_pairs', [])
        sections = self.data.get('sections', [])

        total_qa_pairs = len(qa_pairs)
        unique_sections = len(set([qa.get('section', '') for qa in qa_pairs]))

        context_lengths = [len(qa.get('context', '')) for qa in qa_pairs]
        avg_context_length = sum(context_lengths) / len(context_lengths) if context_lengths else 0

        return {
            'total_qa_pairs': total_qa_pairs,
            'unique_qa_sections': unique_sections,
            'avg_context_length': avg_context_length,
            'total_sections': len(sections)
        }

    def visualize_benchmark(self) -> Tuple[Optional[go.Figure], Optional[go.Figure]]:
        if not self.data:
            return None, None

        qa_pairs = self.data.get('qa_pairs', [])
        if not qa_pairs:
            return None, None

        df = pd.DataFrame(qa_pairs)

        figures = []

        try:
            if 'section' in df.columns:
                section_counts = df['section'].value_counts()
                fig1 = px.bar(
                    x=section_counts.index,
                    y=section_counts.values,
                    title=" Распределение QA пар по секциям",
                    labels={'x': 'Секция', 'y': 'Количество QA пар'}
                )
                fig1.update_layout(xaxis_tickangle=-45)
                figures.append(fig1)
            else:
                figures.append(None)
        except Exception as e:
            print(f"Ошибка создания графика секций: {e}")
            figures.append(None)

        try:
            if 'context' in df.columns:
                df['context_length'] = df['context'].str.len()
                fig2 = px.histogram(
                    df,
                    x='context_length',
                    title="� Распределение длины контекста",
                    labels={'context_length': 'Длина контекста (символы)'}
                )
                figures.append(fig2)
            else:
                figures.append(None)
        except Exception as e:
            print(f"Ошибка создания графика длины: {e}")
            figures.append(None)

        return tuple(figures) if figures else (None, None)


def export_benchmark_report(analyzer: BenchmarkAnalyzer, output_path: str = "benchmark_report.html"):
    try:
        stats = analyzer.get_basic_stats()

        report_html = f"""
        <html>
        <head>
            <title>Отчет по бенчмарку Транснефть</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .stats {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .metric {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>📊 Отчет по бенчмарку Транснефть QA</h1>
            <div class="stats">
                <h2>Основная статистика</h2>
                <div class="metric"><strong>Всего QA пар:</strong> {stats['total_qa_pairs']}</div>
                <div class="metric"><strong>Уникальные секции:</strong> {stats['unique_qa_sections']}</div>
                <div class="metric"><strong>Средняя длина контекста:</strong> {stats['avg_context_length']:.0f} симв.</div>
            </div>
        </body>
        </html>
        """

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_html)

        return True
    except Exception as e:
        print(f"Ошибка экспорта отчета: {e}")
        return False