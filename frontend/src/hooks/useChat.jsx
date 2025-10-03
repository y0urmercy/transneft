import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { chatAPI } from "../services/api";

const ChatContext = createContext();

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};

export const ChatProvider = ({ children }) => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [systemReady, setSystemReady] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);

  // Генерация ID сессии
  const generateSessionId = useCallback(() => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Инициализация системы
  const initializeSystem = useCallback(async () => {
    try {
      const response = await chatAPI.initialize();
      if (response.data.success) {
        setSystemReady(true);
        setError(null);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError("Ошибка инициализации системы");
      console.error("System initialization failed:", err);
    }
  }, []);

  // Загрузка истории чата
  const loadChatHistory = useCallback(async (sId) => {
    try {
      const response = await chatAPI.getChatHistory(sId);
      if (response.data.messages) {
        setMessages(response.data.messages);
      }
    } catch (err) {
      console.error("Failed to load chat history:", err);
    }
  }, []);

  // Отправка сообщения
  const sendMessage = useCallback(
    async (message) => {
      if (!systemReady || !sessionId) return;

      const userMessage = {
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
        id: Date.now(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const response = await chatAPI.sendMessage({
          question: message,
          session_id: sessionId,
          user_id: "user",
        });

        const botMessage = {
          role: "assistant",
          content: response.data.result,
          sources: response.data.source_documents,
          timestamp: new Date().toISOString(),
          confidence: response.data.confidence,
          id: Date.now() + 1,
        };

        setMessages((prev) => [...prev, botMessage]);

        // Обновляем историю
        await loadChatHistory(sessionId);
      } catch (err) {
        const errorMessage = {
          role: "assistant",
          content: `Ошибка: ${err.response?.data?.detail || err.message}`,
          timestamp: new Date().toISOString(),
          isError: true,
          id: Date.now() + 1,
        };
        setMessages((prev) => [...prev, errorMessage]);
        setError(err.response?.data?.detail || "Ошибка отправки сообщения");
      } finally {
        setIsLoading(false);
      }
    },
    [systemReady, sessionId, loadChatHistory]
  );

  // Очистка чата
  const clearChat = useCallback(() => {
    setMessages([]);
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    localStorage.setItem("currentSession", newSessionId);
  }, [generateSessionId]);

  // Инициализация при загрузке
  useEffect(() => {
    const initialize = async () => {
      // Восстанавливаем сессию или создаем новую
      const savedSession = localStorage.getItem("currentSession");
      const newSessionId = savedSession || generateSessionId();
      setSessionId(newSessionId);

      if (!savedSession) {
        localStorage.setItem("currentSession", newSessionId);
      }

      await initializeSystem();
      await loadChatHistory(newSessionId);
    };

    initialize();
  }, [generateSessionId, initializeSystem, loadChatHistory]);

  const value = {
    messages,
    sendMessage,
    isLoading,
    systemReady,
    sessionId,
    error,
    clearChat,
    initializeSystem,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
