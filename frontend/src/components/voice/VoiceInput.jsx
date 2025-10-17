import { useState, useEffect } from "react";
import { Mic, Square } from "lucide-react";

const VoiceInput = ({ onTranscript }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");

  useEffect(() => {
    if (
      !("webkitSpeechRecognition" in window) &&
      !("SpeechRecognition" in window)
    ) {
      console.error("Браузер не поддерживает распознавание речи");
      return;
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "ru-RU";

    recognition.onresult = (event) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      setTranscript(finalTranscript || interimTranscript);
      if (finalTranscript) {
        onTranscript(finalTranscript);
      }
    };

    recognition.onerror = (event) => {
      console.error("Ошибка распознавания:", event.error);
      setIsListening(false);
    };

    if (isListening) {
      recognition.start();
    } else {
      recognition.stop();
    }

    return () => {
      recognition.stop();
    };
  }, [isListening, onTranscript]);

  const toggleListening = () => {
    setIsListening(!isListening);
    if (!isListening) {
      setTranscript("");
    }
  };

  return (
    <div className="voice-input">
      <button
        onClick={toggleListening}
        className={`p-3 rounded-full ${
          isListening ? "bg-red-500" : "bg-blue-500"
        } text-white`}
      >
        {isListening ? <Square size={20} /> : <Mic size={20} />}
      </button>
      {transcript && (
        <div className="mt-2 p-2 bg-gray-100 rounded">{transcript}</div>
      )}
    </div>
  );
};

export default VoiceInput;
