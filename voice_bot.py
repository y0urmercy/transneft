#!/usr/bin/env python3
"""
Голосовой интерфейс для чат-бота Транснефть
"""

import os
import sys
import logging
from typing import Optional

# Добавляем пути для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from speech.modules.stt_module import SpeechToText
from speech.modules.tts_module import TextToSpeech
from speech.modules.asr_module import AutomaticSpeechRecognition

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceBot:
    """
    Голосовой интерфейс для чат-бота
    """
    
    def __init__(self):
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.asr = AutomaticSpeechRecognition()
        self.is_running = False
        
        logger.info("Голосовой бот инициализирован")
    
    def process_text_query(self, text: str) -> str:
        """
        Обрабатывает текстовый запрос и возвращает ответ
        TODO: Интегрировать с вашей основной моделью чат-бота
        
        Args:
            text: Входной текст запроса
            
        Returns:
            Ответ бота
        """
        # Временная заглушка - здесь нужно интегрировать с вашей основной моделью
        responses = {
            "привет": "Здравствуйте! Я голосовой помощник Транснефть. Чем могу помочь?",
            "как дела": "У меня всё отлично! Готов помочь вам с информацией о компании Транснефть.",
            "транснефть": "ПАО 'Транснефть' - российская трубопроводная компания, основанная в 1993 году.",
            "трубопровод": "Протяженность трубопроводов ПАО 'Транснефть' составляет более 67 000 км.",
            "спасибо": "Пожалуйста! Обращайтесь, если потребуется дополнительная информация."
        }
        
        text_lower = text.lower()
        for key, response in responses.items():
            if key in text_lower:
                return response
        
        return "Извините, я еще учусь. Пока могу ответить на вопросы о компании Транснефть, трубопроводах и основной деятельности."
    
    def interactive_mode(self):
        """Интерактивный режим с голосовым вводом/выводом"""
        logger.info("Запуск интерактивного голосового режима")
        self.tts.speak("Голосовой помощник Транснефть активирован. Скажите ваш вопрос.")
        
        self.is_running = True
        
        while self.is_running:
            try:
                # Слушаем вопрос
                question = self.stt.listen_and_transcribe()
                
                if question:
                    logger.info(f"Вопрос пользователя: {question}")
                    
                    # Обрабатываем запрос
                    response = self.process_text_query(question)
                    logger.info(f"Ответ бота: {response}")
                    
                    # Озвучиваем ответ
                    self.tts.speak(response)
                    
                    # Проверяем стоп-фразу
                    if any(phrase in question.lower() for phrase in ['стоп', 'выход', 'закончить']):
                        self.tts.speak("До свидания! Было приятно помочь.")
                        self.is_running = False
                
            except KeyboardInterrupt:
                logger.info("Работа прервана пользователем")
                self.tts.speak("Работа завершена.")
                break
            except Exception as e:
                logger.error(f"Ошибка в интерактивном режиме: {e}")
                self.tts.speak("Произошла ошибка. Попробуйте еще раз.")
    
    def continuous_mode(self):
        """Непрерывный режим прослушивания"""
        logger.info("Запуск непрерывного режима прослушивания")
        
        def process_detected_speech(text: str):
            """Обрабатывает обнаруженную речь"""
            response = self.process_text_query(text)
            self.tts.speak(response)
        
        self.asr.continuous_listen(process_detected_speech)

def main():
    """Основная функция"""
    print("=" * 50)
    print("Голосовой помощник Транснефть")
    print("=" * 50)
    print("Режимы работы:")
    print("1 - Интерактивный режим")
    print("2 - Непрерывное прослушивание")
    print("3 - Тест распознавания речи")
    print("4 - Тест синтеза речи")
    print("0 - Выход")
    
    bot = VoiceBot()
    
    while True:
        try:
            choice = input("\nВыберите режим (0-4): ").strip()
            
            if choice == '0':
                print("Выход из программы.")
                break
            elif choice == '1':
                bot.interactive_mode()
            elif choice == '2':
                bot.continuous_mode()
            elif choice == '3':
                test_speech_recognition(bot)
            elif choice == '4':
                test_speech_synthesis(bot)
            else:
                print("Неверный выбор. Попробуйте снова.")
                
        except KeyboardInterrupt:
            print("\nПрограмма завершена.")
            break
        except Exception as e:
            logger.error(f"Ошибка: {e}")

def test_speech_recognition(bot: VoiceBot):
    """Тестирование распознавания речи"""
    print("\nТест распознавания речи...")
    print("Говорите после сигнала...")
    
    text = bot.stt.listen_and_transcribe()
    if text:
        print(f"Распознано: {text}")
    else:
        print("Речь не распознана")

def test_speech_synthesis(bot: VoiceBot):
    """Тестирование синтеза речи"""
    text = input("Введите текст для озвучивания: ")
    bot.tts.speak(text)
    print("Текст озвучен")

if __name__ == "__main__":
    main()