import pyttsx3
from gtts import gTTS
import tempfile
import os
import logging
from typing import Optional

class TextToSpeech:
    """
    Модуль преобразования текста в речь
    """
    
    def __init__(self, use_online: bool = False, language: str = "ru"):
        self.use_online = use_online
        self.language = language
        self.logger = logging.getLogger(__name__)
        
        if not use_online:
            self._init_offline_engine()
    
    def _init_offline_engine(self):
        """Инициализация оффлайн движка TTS"""
        try:
            self.engine = pyttsx3.init()
            
            # Настройка параметров голоса
            voices = self.engine.getProperty('voices')
            if voices:
                # Попробуем найти русский голос
                for voice in voices:
                    if 'russian' in voice.name.lower() or 'russian' in voice.id.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            
            # Настройка скорости и громкости
            self.engine.setProperty('rate', 150)  # Скорость речи
            self.engine.setProperty('volume', 0.8)  # Громкость (0.0 до 1.0)
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации TTS движка: {e}")
            self.use_online = True  # Переключаемся на онлайн если оффлайн не работает
    
    def speak(self, text: str) -> bool:
        """
        Преобразует текст в речь и воспроизводит
        
        Args:
            text: Текст для озвучивания
            
        Returns:
            True если успешно, False при ошибке
        """
        try:
            if self.use_online:
                return self._speak_online(text)
            else:
                return self._speak_offline(text)
        except Exception as e:
            self.logger.error(f"Ошибка воспроизведения речи: {e}")
            return False
    
    def _speak_offline(self, text: str) -> bool:
        """Оффлайн синтез речи"""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            self.logger.error(f"Ошибка оффлайн TTS: {e}")
            return False
    
    def _speak_online(self, text: str) -> bool:
        """Онлайн синтез речи через Google TTS"""
        try:
            tts = gTTS(text=text, lang=self.language, slow=False)
            
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                tmp_file_path = tmp_file.name
            
            # Воспроизводим файл
            os.system(f"start {tmp_file_path}" if os.name == 'nt' else f"afplay {tmp_file_path}")
            
            # Удаляем временный файл после использования
            import time
            time.sleep(1)  # Даем время на воспроизведение
            os.unlink(tmp_file_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка онлайн TTS: {e}")
            return False
    
    def save_to_file(self, text: str, filename: str) -> bool:
        """
        Сохраняет синтезированную речь в файл
        
        Args:
            text: Текст для синтеза
            filename: Имя файла для сохранения
            
        Returns:
            True если успешно
        """
        try:
            if self.use_online:
                tts = gTTS(text=text, lang=self.language, slow=False)
                tts.save(filename)
            else:
                self.engine.save_to_file(text, filename)
                self.engine.runAndWait()
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения аудио: {e}")
            return False