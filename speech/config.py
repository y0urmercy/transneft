"""
Конфигурация голосового модуля
"""

# Настройки Speech-to-Text
STT_CONFIG = {
    'language': 'ru-RU',
    'timeout': 5,
    'phrase_time_limit': 10,
    'energy_threshold': 300
}

# Настройки Text-to-Speech
TTS_CONFIG = {
    'language': 'ru',
    'use_online': False,  # Использовать онлайн TTS (True) или оффлайн (False)
    'rate': 150,  # Скорость речи
    'volume': 0.8  # Громкость
}

# Настройки ASR
ASR_CONFIG = {
    'silence_duration': 2,
    'stop_phrase': 'стоп'
}

# Настройки аудио
AUDIO_CONFIG = {
    'sample_rate': 16000,
    'channels': 1,
    'chunk_size': 1024
}