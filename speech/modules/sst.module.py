import speech_recognition as sr
import logging
from typing import Optional, Dict, Any

class SpeechToText:
    """
    Модуль преобразования речи в текст
    """
    
    def __init__(self, language: str = "ru-RU"):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.language = language
        self.logger = logging.getLogger(__name__)
        
        # Калибровка микрофона для фонового шума
        self._calibrate_microphone()
    
    def _calibrate_microphone(self):
        """Калибровка микрофона для учета фонового шума"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.logger.info("Микрофон откалиброван")
        except Exception as e:
            self.logger.warning(f"Ошибка калибровки микрофона: {e}")
    
    def listen_and_transcribe(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Прослушивает аудио и преобразует в текст
        
        Args:
            timeout: Время ожидания речи (секунды)
            phrase_time_limit: Максимальная длина фразы (секунды)
            
        Returns:
            Распознанный текст или None при ошибке
        """
        try:
            with self.microphone as source:
                self.logger.info("Слушаю...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            
            self.logger.info("Обрабатываю аудио...")
            text = self.recognizer.recognize_google(audio, language=self.language)
            self.logger.info(f"Распознано: {text}")
            return text
            
        except sr.WaitTimeoutError:
            self.logger.info("Время ожидания истекло")
            return None
        except sr.UnknownValueError:
            self.logger.warning("Речь не распознана")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Ошибка сервиса распознавания: {e}")
            return None
    
    def transcribe_audio_file(self, audio_file_path: str) -> Optional[str]:
        """
        Преобразует аудиофайл в текст
        
        Args:
            audio_file_path: Путь к аудиофайлу
            
        Returns:
            Распознанный текст
        """
        try:
            with sr.AudioFile(audio_file_path) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language=self.language)
                return text
        except Exception as e:
            self.logger.error(f"Ошибка обработки аудиофайла: {e}")
            return None