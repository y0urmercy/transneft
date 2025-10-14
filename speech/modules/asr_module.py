import numpy as np
import logging
from typing import Optional, Callable

class VoiceActivityDetector:
    """
    Детектор речевой активности для ASR
    """
    
    def __init__(self, energy_threshold: float = 300, silence_duration: int = 2):
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
        self.logger = logging.getLogger(__name__)
    
    def detect_voice_activity(self, audio_data: np.ndarray) -> bool:
        """
        Определяет наличие речевой активности в аудиоданных
        
        Args:
            audio_data: Аудиоданные для анализа
            
        Returns:
            True если обнаружена речь
        """
        try:
            # Простая проверка энергии сигнала
            energy = np.sum(audio_data.astype(float) ** 2) / len(audio_data)
            return energy > self.energy_threshold
        except Exception as e:
            self.logger.error(f"Ошибка детектирования речи: {e}")
            return False

class AutomaticSpeechRecognition:
    """
    Автоматическое распознавание речи с детектированием активности
    """
    
    def __init__(self):
        self.stt = SpeechToText()
        self.vad = VoiceActivityDetector()
        self.logger = logging.getLogger(__name__)
    
    def continuous_listen(self, callback: Callable[[str], None], stop_phrase: str = "стоп"):
        """
        Непрерывное прослушивание с вызовом callback при обнаружении речи
        
        Args:
            callback: Функция, вызываемая с распознанным текстом
            stop_phrase: Фраза для остановки прослушивания
        """
        self.logger.info("Запуск непрерывного прослушивания. Скажите 'стоп' для выхода.")
        
        while True:
            try:
                text = self.stt.listen_and_transcribe(timeout=1, phrase_time_limit=5)
                
                if text:
                    text_lower = text.lower()
                    self.logger.info(f"Распознано: {text}")
                    
                    # Проверяем стоп-фразу
                    if stop_phrase in text_lower:
                        self.logger.info("Обнаружена стоп-фраза. Завершение работы.")
                        break
                    
                    # Вызываем callback с распознанным текстом
                    callback(text)
                    
            except KeyboardInterrupt:
                self.logger.info("Прервано пользователем")
                break
            except Exception as e:
                self.logger.error(f"Ошибка в непрерывном режиме: {e}")
                continue