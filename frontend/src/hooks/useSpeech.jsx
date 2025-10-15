import { useState, useCallback } from "react";

export const useSpeech = () => {
  const [isSpeaking, setIsSpeaking] = useState(false);

  const speak = useCallback((text) => {
    if (!("speechSynthesis" in window)) {
      console.error("Браузер не поддерживает синтез речи");
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ru-RU";
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  }, []);

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  return { speak, stop, isSpeaking };
};
