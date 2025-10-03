import React, { useState, useEffect } from "react";
import { chatAPI } from "../services/api";
import { useChat } from "../hooks/useChat";

const History = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessionMessages, setSessionMessages] = useState([]);
  const { sessionId: currentSessionId, clearChat } = useChat();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      // В реальном приложении здесь будет API для получения сессий
      // Пока используем mock данные
      const mockSessions = [
        {
          session_id: currentSessionId,
          start_time: new Date().toISOString(),
          message_count: 5,
          last_message: "Последний вопрос о деятельности компании",
        },
        {
          session_id: "session_123456",
          start_time: new Date(Date.now() - 86400000).toISOString(),
          message_count: 3,
          last_message: "Вопросы по уставному капиталу",
        },
      ];
      setSessions(mockSessions);
    } catch (error) {
      console.error("Error loading sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadSessionMessages = async (sessionId) => {
    try {
      const response = await chatAPI.getChatHistory(sessionId);
      setSessionMessages(response.data.messages || []);
      setSelectedSession(sessionId);
    } catch (error) {
      console.error("Error loading session messages:", error);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const exportChatHistory = (sessionId) => {
    const session = sessions.find((s) => s.session_id === sessionId);
    const data = {
      session_id: sessionId,
      export_date: new Date().toISOString(),
      message_count: session?.message_count || 0,
      messages: sessionMessages,
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `chat_history_${sessionId.slice(0, 8)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">📊 История сессий</h1>
        <button onClick={clearChat} className="btn-secondary">
          🆕 Новая сессия
        </button>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="metric-card">
          <h3 className="text-sm font-medium text-gray-500">Всего сессий</h3>
          <p className="text-2xl font-bold text-gray-900">{sessions.length}</p>
        </div>
        <div className="metric-card">
          <h3 className="text-sm font-medium text-gray-500">Всего сообщений</h3>
          <p className="text-2xl font-bold text-gray-900">
            {sessions.reduce(
              (total, session) => total + session.message_count,
              0
            )}
          </p>
        </div>
        <div className="metric-card">
          <h3 className="text-sm font-medium text-gray-500">Текущая сессия</h3>
          <p className="text-lg font-semibold text-blue-600">
            {currentSessionId?.slice(0, 8)}...
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Список сессий */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Предыдущие сессии
          </h2>
          {sessions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>Нет сохраненных сессий</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.session_id}
                className={`metric-card cursor-pointer transition-all hover:shadow-md ${
                  selectedSession === session.session_id
                    ? "ring-2 ring-blue-500"
                    : ""
                }`}
                onClick={() => loadSessionMessages(session.session_id)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-900">
                      Сессия {session.session_id.slice(0, 8)}...
                      {session.session_id === currentSessionId && (
                        <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                          текущая
                        </span>
                      )}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {formatDate(session.start_time)}
                    </p>
                    <p className="text-sm text-gray-600 mt-2">
                      {session.last_message}
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-blue-600">
                      {session.message_count}
                    </div>
                    <div className="text-xs text-gray-500">сообщений</div>
                  </div>
                </div>

                <div className="flex space-x-2 mt-3">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      loadSessionMessages(session.session_id);
                    }}
                    className="btn-secondary text-xs"
                  >
                    📝 Просмотреть
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      exportChatHistory(session.session_id);
                    }}
                    className="btn-secondary text-xs"
                  >
                    📤 Экспорт
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Сообщения выбранной сессии */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {selectedSession
              ? `Сообщения сессии ${selectedSession.slice(0, 8)}...`
              : "Выберите сессию"}
          </h2>

          {selectedSession ? (
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {sessionMessages.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>Нет сообщений в этой сессии</p>
                </div>
              ) : (
                sessionMessages.map((message, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg ${
                      message.role === "user"
                        ? "bg-blue-50 border border-blue-200 ml-8"
                        : "bg-gray-50 border border-gray-200 mr-8"
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          message.role === "user"
                            ? "bg-blue-100"
                            : "bg-gray-100"
                        }`}
                      >
                        {message.role === "user" ? "👤" : "🤖"}
                      </div>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-gray-900">
                          {message.role === "user" ? "Вы" : "Ассистент"}
                        </div>
                        <div className="text-sm text-gray-700 mt-1">
                          {message.content}
                        </div>
                        <div className="text-xs text-gray-500 mt-2">
                          {formatDate(message.timestamp)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <div className="text-4xl mb-4">📋</div>
              <p>Выберите сессию для просмотра истории сообщений</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default History;
