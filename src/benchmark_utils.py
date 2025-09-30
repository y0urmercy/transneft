import json
import pandas as pd
import plotly.express as px
from typing import Dict, List, Any
import streamlit as st

class BenchmarkAnalyzer:
    """Анализатор бенчмарка Транснефть"""
    
    def __init__(self, benchmark_path: str):
        self.benchmark_path = benchmark_path
        self.data = self.load_benchmark()
    
    def load_benchmark(self) -> Dict[str, Any]:
        """Загрузка бенчмарка"""
        try:
            with open(self.benchmark_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Ошибка загрузки бенчмарка: {e}")
            return {}
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Базовая статистика бенчмарка"""
        if not self.data:
            return {}
        
        qa_pairs = self.data.get('qa_pairs', [])
        sections = self.data.get('sections', [])
        
        stats = {
            'total_qa_pairs': len(qa_pairs),
            'total_sections': len(sections),
            'unique_qa_sections': len(set([qa['section'] for qa in qa_pairs])),
            'avg_context_length': np.mean([qa.get('context_length', 0) for qa in qa_pairs]),
            'total_words': sum([qa.get('word_count', 0) for qa in qa_pairs]),
            'sections_with_entities': len([qa for qa in qa_pairs if qa.get('entities')])
        }
        
        return stats
    
    def get_section_analysis(self) -> pd.DataFrame:
        """Анализ распределения по секциям"""
        qa_pairs = self.data.get('qa_pairs', [])
        
        section_data = {}
        for qa in qa_pairs:
            section = qa['section']
            if section not in section_data:
                section_data[section] = {
                    'count': 0,
                    'total_context_length': 0,
                    'has_entities': 0
                }
            
            section_data[section]['count'] += 1
            section_data[section]['total_context_length'] += qa.get('context_length', 0)
            if qa.get('entities'):
                section_data[section]['has_entities'] += 1
        
        # Создание DataFrame
        analysis_data = []
        for section, data in section_data.items():
            analysis_data.append({
                'section': section,
                'qa_count': data['count'],
                'avg_context_length': data['total_context_length'] / data['count'],
                'with_entities': data['has_entities'],
                'entity_percentage': (data['has_entities'] / data['count']) * 100
            })
        
        return pd.DataFrame(analysis_data).sort_values('qa_count', ascending=False)
    
    def visualize_benchmark(self):
        """Визуализация структуры бенчмарка"""
        if not self.data:
            return None, None
        
        # Анализ секций
        section_df = self.get_section_analysis()
        
        # Топ-15 секций по количеству QA пар
        top_sections = section_df.head(15)
        fig1 = px.bar(
            top_sections, 
            x='section', 
            y='qa_count',
            title="Топ-15 секций по количеству QA пар",
            labels={'section': 'Секция', 'qa_count': 'Количество QA пар'}
        )
        fig1.update_layout(xaxis_tickangle=-45)
        
        # Распределение длины контекста
        context_lengths = [qa.get('context_length', 0) for qa in self.data.get('qa_pairs', [])]
        fig2 = px.histogram(
            x=context_lengths,
            title="Распределение длины контекста",
            labels={'x': 'Длина контекста (символы)', 'y': 'Количество'}
        )
        
        return fig1, fig2
    
    def get_entity_analysis(self) -> Dict[str, Any]:
        """Анализ сущностей в бенчмарке"""
        qa_pairs = self.data.get('qa_pairs', [])
        
        all_entities = []
        entities_per_section = {}
        
        for qa in qa_pairs:
            entities = qa.get('entities', [])
            all_entities.extend(entities)
            
            section = qa['section']
            if section not in entities_per_section:
                entities_per_section[section] = []
            entities_per_section[section].extend(entities)
        
        # Анализ частотности сущностей
        from collections import Counter
        entity_freq = Counter(all_entities)
        
        return {
            'total_entities': len(all_entities),
            'unique_entities': len(entity_freq),
            'top_entities': entity_freq.most_common(20),
            'entities_per_section': {k: len(v) for k, v in entities_per_section.items()}
        }

def export_benchmark_report(benchmark_path: str, output_dir: str = "results"):
    """Экспорт полного отчета по бенчмарку"""
    analyzer = BenchmarkAnalyzer(benchmark_path)
    
    # Базовая статистика
    stats = analyzer.get_basic_stats()
    
    # Анализ секций
    section_df = analyzer.get_section_analysis()
    
    # Анализ сущностей
    entity_analysis = analyzer.get_entity_analysis()
    
    # Сохранение в CSV
    section_df.to_csv(f"{output_dir}/section_analysis.csv", index=False, encoding='utf-8')
    
    # Сохранение статистики
    stats_df = pd.DataFrame([stats])
    stats_df.to_csv(f"{output_dir}/benchmark_stats.csv", index=False)
    
    return {
        'stats': stats,
        'section_analysis': section_df,
        'entity_analysis': entity_analysis
    }