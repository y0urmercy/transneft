import unittest
import os
import tempfile
from speech.modules.stt_module import SpeechToText

class TestSpeechToText(unittest.TestCase):
    
    def setUp(self):
        self.stt = SpeechToText()
    
    def test_initialization(self):
        """Тест инициализации модуля"""
        self.assertIsNotNone(self.stt.recognizer)
        self.assertIsNotNone(self.stt.microphone)
        self.assertEqual(self.stt.language, "ru-RU")

if __name__ == '__main__':
    unittest.main()