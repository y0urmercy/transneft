"""
UI компоненты в стиле Госуслуг для Streamlit
"""

import streamlit as st
import os
import uuid
from PIL import Image
import base64
from typing import Optional, Dict, Any
from datetime import datetime
import pandas as pd
import plotly.express as px

class GosuslugiUI:
    """Класс для создания UI компонентов в стиле Госуслуг"""
    
    @staticmethod
    def load_css(css_file_path: str = "css/gosuslugi_style.css"):
        """Загрузка CSS стилей из файла"""
        try:
            if os.path.exists(css_file_path):
                with open(css_file_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
            else:
                st.warning(f"CSS файл не найден: {css_file_path}")
        except Exception as e:
            st.error(f"Ошибка загрузки CSS: {e}")
    
    @staticmethod
    def create_header(user_name: str = "Пользователь"):
        """Создание шапки в стиле Госуслуг"""
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="main-header">
                <h1 style="margin:0; font-size: 2rem;">🤖 Помощник ПАО "Транснефть"</h1>
                <p style="margin:0; opacity: 0.9; font-size: 1.1rem;">Экспертная система вопросов и ответов</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            GosuslugiUI.display_user_profile(user_name)
    
    @staticmethod
    def display_user_profile(user_name: str = "Пользователь"):
        """Отображение профиля пользователя с аватаром"""
        avatar_path = "assets/user_avatar.png"
        
        # Создаем папку assets если её нет
        os.makedirs("assets", exist_ok=True)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Аватар пользователя
            if os.path.exists(avatar_path):
                try:
                    image = Image.open(avatar_path)
                    st.image(image, width=50, use_column_width=False)
                except Exception as e:
                    st.error(f"Ошибка загрузки аватара: {e}")
                    GosuslugiUI._display_default_avatar()
            else:
                GosuslugiUI._display_default_avatar()
        
        with col2:
            st.markdown(f"""
            <div style="text-align: left;">
                <p style="margin: 0; font-weight: 600; font-size: 0.9rem;">{user_name}</p>
                <p style="margin: 0; font-size: 0.8rem; color: #666;">Профиль</p>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def _display_default_avatar():
        """Отображение дефолтного аватара"""
        st.markdown("""
        <div style="text-align: center;">
            <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #1e6cde 0%, #0d4ba3 100%); 
                 border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                 margin: 0 auto; color: white; font-weight: bold; font-size: 18px;">
                👤
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def upload_avatar():
        """Компонент для загрузки аватара"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("🖼️ Настройки профиля")
        
        uploaded_file = st.sidebar.file_uploader(
            "Загрузите аватар", 
            type=['png', 'jpg', 'jpeg'],
            help="Рекомендуемый размер: 200x200 пикселей"
        )
        
        if uploaded_file is not None:
            try:
                # Сохраняем загруженный файл
                avatar_path = "assets/user_avatar.png"
                with open(avatar_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.sidebar.success("✅ Аватар успешно загружен!")
                
                # Показываем превью
                image = Image.open(uploaded_file)
                st.sidebar.image(image, width=100, caption="Ваш новый аватар")
                
            except Exception as e:
                st.sidebar.error(f"Ошибка загрузки аватаar: {e}")
    
    @staticmethod
    def create_search_section():
        """Создание секции поиска в стиле Госуслуг"""
        st.markdown("""
        <div class="search-container">
            <h3 style="margin-top: 0;">🔍 Поиск информации о ПАО "Транснефть"</h3>
            <p style="color: #666; margin-bottom: 1.5rem;">
                Задайте вопрос о компании, её деятельности, финансах или проектах
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def display_chat_message(message: str, is_user: bool = True, timestamp: str = None):
        """Отображение сообщения в чате"""
        message_class = "chat-message-user" if is_user else "chat-message-bot"
        icon = "👤" if is_user else "🤖"
        
        timestamp_html = f'<small style="opacity: 0.7; font-size: 0.8rem;">{timestamp}</small>' if timestamp else ""
        
        st.markdown(f"""
        <div class="{message_class}">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="margin-right: 0.5rem;">{icon}</span>
                <strong>{'Вы' if is_user else 'Помощник Транснефть'}</strong>
            </div>
            <div style="line-height: 1.5;">{message}</div>
            {timestamp_html}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def display_source_documents(sources: list, max_display: int = 3):
        """Отображение источников информации"""
        if sources:
            st.markdown("**📚 Источники информации:**")
            for i, source in enumerate(sources[:max_display]):
                if isinstance(source, dict):
                    source_content = source.get('content', '')[:150] + "..." if len(source.get('content', '')) > 150 else source.get('content', '')
                    source_section = source.get('section', 'Неизвестно')
                else:
                    source_content = source.page_content[:150] + "..." if len(source.page_content) > 150 else source.page_content
                    source_section = getattr(source, 'metadata', {}).get('section', 'Неизвестно')
                
                st.markdown(f"""
                <div class="source-card">
                    <strong>🔹 Источник {i+1}</strong> ({source_section})
                    <br>
                    <span style="font-size: 0.9rem;">{source_content}</span>
                </div>
                """, unsafe_allow_html=True)
    
    @staticmethod
    def create_service_card(title: str, description: str, icon: str = "📋"):
        """Создание карточки услуги в стиле Госуслуг"""
        st.markdown(f"""
        <div class="service-card">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
                <h4 style="margin: 0;">{title}</h4>
            </div>
            <p style="margin: 0; color: #666;">{description}</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def display_metric_card(title: str, value: Any, delta: str = None, help_text: str = None):
        """Отображение карточки с метрикой"""
        delta_html = f"<br><small>{delta}</small>" if delta else ""
        help_html = f'<br><small style="color: #666;">{help_text}</small>' if help_text else ""
        
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="margin: 0 0 0.5rem 0; color: #333;">{title}</h4>
            <h2 style="margin: 0; color: #1e6cde;">{value}</h2>
            {delta_html}
            {help_html}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_sidebar_navigation():
        """Создание навигации в сайдбаре"""
        st.sidebar.markdown("""
        <div class="sidebar-header">
            <h3 style="margin: 0;">🎯 Навигация</h3>
            <p style="margin: 0; opacity: 0.9;">Система Транснефть QA</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def display_system_status(status: str, message: str):
        """Отображение статуса системы"""
        status_class = {
            "ready": "system-status-ready",
            "loading": "system-status-loading", 
            "error": "system-status-error"
        }.get(status, "system-status-loading")
        
        st.markdown(f"""
        <div class="{status_class}" style="text-align: center;">
            {message}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def create_quick_actions():
        """Создание блока быстрых действий"""
        st.markdown("### 🚀 Быстрые действия")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Оценить систему", use_container_width=True):
                st.session_state.current_tab = "Оценка качества"
                st.rerun()
        
        with col2:
            if st.button("📈 Аналитика", use_container_width=True):
                st.session_state.current_tab = "Аналитика"
                st.rerun()
        
        with col3:
            if st.button("🔄 Обновить", use_container_width=True):
                st.rerun()


class DatabaseUI:
    """UI компоненты для работы с базой данных"""
    
    @staticmethod
    def display_chat_history_controls():
        """Элементы управления историей чата"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Сохранить сессию", use_container_width=True):
                st.session_state.save_session = True
        
        with col2:
            if st.button("📊 Статистика", use_container_width=True):
                st.session_state.show_stats = True
        
        with col3:
            if st.button("🔄 Новая сессия", use_container_width=True):
                st.session_state.current_session = str(uuid.uuid4())
                st.session_state.chat_history = []
                st.rerun()
    
    @staticmethod
    def display_feedback_form(message_id: int):
        """Форма для оценки ответа"""
        with st.expander("💬 Оценить ответ"):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                rating = st.selectbox(
                    "Оценка:",
                    [1, 2, 3, 4, 5],
                    format_func=lambda x: "⭐" * x,
                    key=f"rating_{message_id}"
                )
            
            with col2:
                feedback = st.text_area(
                    "Комментарий:",
                    placeholder="Что можно улучшить?",
                    key=f"feedback_{message_id}",
                    height=60
                )
            
            if st.button("📨 Отправить отзыв", key=f"submit_feedback_{message_id}"):
                try:
                    from database_models import db_manager
                    db_manager.add_feedback(message_id, rating, feedback)
                    st.success("✅ Спасибо за ваш отзыв!")
                except Exception as e:
                    st.error(f"❌ Ошибка сохранения отзыва: {e}")
    
    @staticmethod
    def display_session_analytics(stats: Dict[str, Any]):
        """Отображение аналитики сессии"""
        st.markdown("### 📈 Статистика чата")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            GosuslugiUI.display_metric_card(
                "Всего сообщений",
                stats.get('total_messages', 0)
            )
        
        with col2:
            GosuslugiUI.display_metric_card(
                "Среднее время ответа",
                f"{stats.get('avg_response_time', 0):.1f}с"
            )
        
        with col3:
            GosuslugiUI.display_metric_card(
                "Оцененных сообщений",
                stats.get('rated_messages', 0)
            )
        
        with col4:
            avg_rating = stats.get('avg_rating', 0)
            GosuslugiUI.display_metric_card(
                "Средняя оценка",
                f"{avg_rating:.1f}⭐" if avg_rating > 0 else "Нет оценок"
            )
        
        # График активности по дням
        if stats.get('daily_stats'):
            df_daily = pd.DataFrame(stats['daily_stats'])
            fig = px.line(
                df_daily, 
                x='date', 
                y='message_count',
                title="Активность по дням",
                labels={'date': 'Дата', 'message_count': 'Сообщений'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def display_export_options():
        """Опции экспорта истории"""
        st.markdown("### 📤 Экспорт истории")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            export_format = st.selectbox(
                "Формат:",
                ["json", "csv"]
            )
        
        with col2:
            export_scope = st.selectbox(
                "Область:",
                ["current_session", "all_sessions"]
            )
        
        with col3:
            if st.button("📥 Экспортировать", use_container_width=True):
                try:
                    from database_models import db_manager
                    
                    session_id = None
                    if export_scope == "current_session":
                        session_id = st.session_state.get('current_session', 'default')
                    
                    exported_data = db_manager.export_chat_history(
                        session_id, 
                        export_format
                    )
                    
                    # Создаем downloadable файл
                    file_extension = export_format
                    mime_type = "application/json" if export_format == "json" else "text/csv"
                    file_name = f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
                    
                    st.download_button(
                        label="💾 Скачать файл",
                        data=exported_data,
                        file_name=file_name,
                        mime=mime_type,
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"❌ Ошибка экспорта: {e}")


class AvatarManager:
    """Менеджер для работы с аватарами"""
    
    @staticmethod
    def get_available_avatars() -> list:
        """Получить список доступных аватаров"""
        avatars_dir = "assets/avatars"
        os.makedirs(avatars_dir, exist_ok=True)
        
        available_avatars = []
        for file in os.listdir(avatars_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                available_avatars.append(os.path.join(avatars_dir, file))
        
        return available_avatars
    
    @staticmethod
    def create_default_avatar():
        """Создание дефолтного аватара"""
        avatar_path = "assets/user_avatar.png"
        os.makedirs("assets", exist_ok=True)
        
        # Создаем простой градиентный аватар
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (200, 200), color='#1e6cde')
            draw = ImageDraw.Draw(img)
            
            # Рисуем простой градиент
            for i in range(200):
                r = int(30 + (225 - 30) * i / 200)
                g = int(108 + (255 - 108) * i / 200)
                b = int(222 + (255 - 222) * i / 200)
                draw.line([(0, i), (200, i)], fill=(r, g, b))
            
            # Рисуем иконку пользователя
            draw.ellipse([50, 50, 150, 150], fill='white')
            draw.ellipse([75, 75, 125, 125], fill='#1e6cde')
            
            img.save(avatar_path)
            return avatar_path
        except Exception as e:
            st.error(f"Ошибка создания аватара: {e}")
            return None
    
    @staticmethod
    def image_to_base64(image_path: str) -> str:
        """Конвертировать изображение в base64"""
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        except:
            return ""