// src/components/chat/ChatInterfaceDebug.jsx
import React, { useState, useRef, useEffect } from "react";
import { useChat } from "../../hooks/useChat";

const ChatInterface = () => {
  const {
    messages,
    sendMessage,
    isLoading,
    systemReady,
    error,
    sessionId,
    initStatus,
    initializeSystem,
  } = useChat();

  const [inputMessage, setInputMessage] = useState("");
  const [debugLog, setDebugLog] = useState([]);
  const messagesEndRef = useRef(null);

  const addDebugLog = (message, type = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setDebugLog((prev) => [...prev, { timestamp, message, type }]);
    console.log(`[${type.toUpperCase()}] ${message}`);
  };

  useEffect(() => {
    addDebugLog("Компонент ChatInterface смонтирован", "info");
    addDebugLog(`systemReady: ${systemReady}`, "info");
    addDebugLog(`initStatus: ${initStatus}`, "info");
    addDebugLog(`sessionId: ${sessionId}`, "info");
    addDebugLog(`messages count: ${messages.length}`, "info");
  }, []);

  useEffect(() => {
    addDebugLog(`systemReady изменился на: ${systemReady}`, "state");
  }, [systemReady]);

  useEffect(() => {
    if (error) {
      addDebugLog(`Ошибка: ${error}`, "error");
    }
  }, [error]);

  useEffect(() => {
    if (initStatus) {
      addDebugLog(`Статус инициализации: ${initStatus}`, "state");
    }
  }, [initStatus]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading) {
      addDebugLog(`Отправка сообщения: "${inputMessage}"`, "action");
      await sendMessage(inputMessage.trim());
      setInputMessage("");
    }
  };

  const handleManualInitialize = async () => {
    addDebugLog("Ручная инициализация системы...", "action");
    const result = await initializeSystem();
    addDebugLog(
      `Ручная инициализация: ${result ? "УСПЕХ" : "ОШИБКА"}`,
      result ? "success" : "error"
    );
  };

  const testAPIEndpoints = async () => {
    addDebugLog("Тестирование API endpoints...", "action");

    try {
      const { chatAPI } = await import("../../services/api");
      const healthResponse = await chatAPI.health();
      addDebugLog(
        `Health endpoint: ${JSON.stringify(healthResponse.data)}`,
        "success"
      );

      const initResponse = await chatAPI.initialize();
      addDebugLog(
        `Initialize endpoint: ${JSON.stringify(initResponse.data)}`,
        "success"
      );
    } catch (err) {
      addDebugLog(`API тест провален: ${err.message}`, "error");
      console.error("API Test Error:", err);
    }
  };

  const clearDebugLog = () => {
    setDebugLog([]);
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-bold text-gray-800">
            Диагностика системы
          </h2>
          <div className="flex space-x-2">
            <button
              onClick={handleManualInitialize}
              className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
            >
              Инициализировать
            </button>
            <button
              onClick={testAPIEndpoints}
              className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
            >
              Тест API
            </button>
            <button
              onClick={clearDebugLog}
              className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600"
            >
              Очистить логи
            </button>
          </div>
        </div>

        {/* Статус системы */}
        <div className="grid grid-cols-4 gap-4 text-sm">
          <div
            className={`p-2 rounded ${
              systemReady
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            <strong>System Ready:</strong> {systemReady ? "✅" : "❌"}
          </div>
          <div className="p-2 rounded bg-blue-100 text-blue-800">
            <strong>Init Status:</strong> {initStatus || "unknown"}
          </div>
          <div className="p-2 rounded bg-purple-100 text-purple-800">
            <strong>Session:</strong>{" "}
            {sessionId ? sessionId.substring(0, 8) + "..." : "none"}
          </div>
          <div
            className={`p-2 rounded ${
              error ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"
            }`}
          >
            <strong>Error:</strong> {error ? "❌" : "✅"}
          </div>
        </div>

        {/* Логи диагностики */}
        <div className="mt-3 max-h-32 overflow-y-auto bg-black text-green-400 p-2 rounded text-xs font-mono">
          {debugLog.slice(-10).map((log, index) => (
            <div
              key={index}
              className={`${
                log.type === "error"
                  ? "text-red-400"
                  : log.type === "success"
                  ? "text-green-400"
                  : "text-yellow-400"
              }`}
            >
              [{log.timestamp}] {log.message}
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-12">
              <div className="text-6xl mb-4">💡</div>
              <p className="text-lg font-medium mb-2">
                Добро пожаловать в помощник ПАО "Транснефть"
              </p>
              <p className="text-gray-600 mb-4">
                Задайте вопрос о компании, её деятельности, финансах или
                проектах
              </p>
              <div className="text-sm text-gray-500">
                Статус системы: {systemReady ? "Готова" : "Инициализация..."}
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`p-4 rounded-lg ${
                  message.role === "user"
                    ? "bg-blue-50 ml-12"
                    : "bg-gray-50 mr-12"
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === "user" ? "bg-blue-500" : "bg-gray-500"
                    }`}
                  >
                    {message.role === "user" ? "👤" : "🤖"}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-sm mb-1">
                      {message.role === "user" ? "Вы" : "Помощник Транснефть"}
                    </div>
                    <div className="text-gray-800">{message.content}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-gray-200 p-6 bg-white">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">⚠️ {error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Например: Каков размер уставного капитала Транснефти? Или: Когда компания была основана?"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="3"
                disabled={isLoading}
              />
            </div>
            <button
              type="submit"
              disabled={!inputMessage.trim() || isLoading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed self-end"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Поиск...
                </div>
              ) : (
                "Отправить"
              )}
            </button>
          </form>

          <div className="mt-3 flex items-center justify-between text-sm">
            <div>
              {!systemReady ? (
                <span className="text-orange-600 flex items-center">
                  <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse mr-2"></div>
                  Система инициализируется... (статус: {initStatus})
                </span>
              ) : (
                <span className="text-green-600 flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  Система готова
                </span>
              )}
            </div>

            {messages.length > 0 && (
              <span className="text-gray-500">
                {messages.filter((m) => m.role === "user").length} сообщений
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
