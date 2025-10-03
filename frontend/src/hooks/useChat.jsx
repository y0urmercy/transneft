// hooks/useChat.js
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
  const [initStatus, setInitStatus] = useState("pending"); // Добавляем для диагностики

  // Генерация ID сессии
  const generateSessionId = useCallback(() => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Инициализация системы с диагностикой
  const initializeSystem = useCallback(async () => {
    try {
      console.log("🔄 Starting system initialization...");
      setInitStatus("initializing");
      setError(null);

      const response = await chatAPI.initialize();
      console.log("✅ Initialize API response:", response);

      if (response.data.status === "success") {
        setSystemReady(true);
        setInitStatus("success");
        console.log("✅ System initialized successfully");
        return true;
      } else {
        const errorMsg =
          response.data.message || "Initialization failed - unknown reason";
        console.error("❌ Initialize failed with message:", errorMsg);
        setError(errorMsg);
        setInitStatus("failed");
        return false;
      }
    } catch (err) {
      console.error("❌ Initialize error details:", err);

      let errorMsg = "Ошибка инициализации системы";
      if (err.response) {
        // Сервер ответил с ошибкой
        errorMsg =
          err.response.data?.detail ||
          `HTTP ${err.response.status}: ${err.response.statusText}`;
        console.error("❌ Server response error:", err.response.data);
      } else if (err.request) {
        // Запрос был сделан, но ответ не получен
        errorMsg =
          "Не удалось подключиться к серверу. Проверьте, запущен ли бэкенд.";
        console.error("❌ No response received:", err.request);
      } else {
        // Что-то пошло не так при настройке запроса
        errorMsg = err.message || "Ошибка настройки запроса";
        console.error("❌ Request setup error:", err.message);
      }

      setError(errorMsg);
      setInitStatus("failed");
      return false;
    }
  }, []);

  // Загрузка истории чата
  const loadChatHistory = useCallback(async (sId) => {
    try {
      console.log("📖 Loading chat history for session:", sId);
      const response = await chatAPI.getChatHistory(sId);
      console.log("✅ History response:", response.data);

      const history = response.data.history || [];
      const formattedMessages = [];

      history.forEach((msg) => {
        if (msg.question) {
          formattedMessages.push({
            id: `user_${msg.message_id || Date.now()}`,
            role: "user",
            content: msg.question,
            timestamp: msg.timestamp || new Date().toISOString(),
          });
        }

        if (msg.answer) {
          formattedMessages.push({
            id: `assistant_${msg.message_id || Date.now() + 1}`,
            role: "assistant",
            content: msg.answer,
            timestamp: msg.timestamp || new Date().toISOString(),
            sources: msg.sources || [],
            confidence: msg.confidence,
          });
        }
      });

      setMessages(formattedMessages);
      console.log(`✅ Loaded ${formattedMessages.length} messages`);
    } catch (err) {
      console.error("❌ Failed to load chat history:", err);
      // Не очищаем сообщения при ошибке
    }
  }, []);

  // Отправка сообщения
  const sendMessage = useCallback(
    async (message) => {
      if (!systemReady) {
        setError("Система не готова. Сначала инициализируйте систему.");
        return;
      }

      if (!sessionId) {
        setError("Сессия не создана");
        return;
      }

      const userMessage = {
        id: `user_${Date.now()}`,
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        console.log("📤 Sending message:", message);
        const response = await chatAPI.sendMessage({
          question: message,
          session_id: sessionId,
        });

        console.log("✅ Message response:", response.data);

        const botMessage = {
          id: `assistant_${Date.now() + 1}`,
          role: "assistant",
          content: response.data.result || "Ответ не получен",
          sources: response.data.source_documents || [],
          timestamp: new Date().toISOString(),
          confidence: response.data.confidence || 0,
        };

        setMessages((prev) => [...prev, botMessage]);
      } catch (err) {
        console.error("❌ Send message error:", err);
        const errorMessage = {
          id: `error_${Date.now() + 1}`,
          role: "assistant",
          content: `Ошибка: ${
            err.response?.data?.detail || err.message || "Неизвестная ошибка"
          }`,
          timestamp: new Date().toISOString(),
          isError: true,
        };
        setMessages((prev) => [...prev, errorMessage]);
        setError(err.response?.data?.detail || "Ошибка отправки сообщения");
      } finally {
        setIsLoading(false);
      }
    },
    [systemReady, sessionId]
  );

  // Очистка чата
  const clearChat = useCallback(() => {
    setMessages([]);
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    localStorage.setItem("currentSession", newSessionId);
    console.log("🧹 Chat cleared, new session:", newSessionId);
  }, [generateSessionId]);

  // Инициализация при загрузке
  useEffect(() => {
    const initialize = async () => {
      console.log("🚀 Initializing chat provider...");

      // Восстанавливаем сессию или создаем новую
      const savedSession = localStorage.getItem("currentSession");
      const newSessionId = savedSession || generateSessionId();
      setSessionId(newSessionId);

      if (!savedSession) {
        localStorage.setItem("currentSession", newSessionId);
      }

      console.log("📝 Session ID:", newSessionId);

      // Инициализируем систему
      await initializeSystem();

      // Загружаем историю только если система готова
      if (systemReady) {
        await loadChatHistory(newSessionId);
      }
    };

    initialize();
  }, [generateSessionId, initializeSystem, loadChatHistory, systemReady]);

  const value = {
    messages,
    sendMessage,
    isLoading,
    systemReady,
    sessionId,
    error,
    clearChat,
    initializeSystem,
    initStatus, // Добавляем для диагностики
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
