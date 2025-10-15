import React, { useState, useEffect } from "react";
import { chatAPI } from "../services/api";
import { useChat } from "../hooks/useChat";

const History = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessionMessages, setSessionMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const { sessionId: currentSessionId, clearChat } = useChat();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setLoading(true);

      const currentSessionResponse = await chatAPI.getChatHistory(
        currentSessionId
      );
      const currentSessionData = currentSessionResponse.data;

      const currentSession = {
        session_id: currentSessionId,
        start_time:
          currentSessionData.history && currentSessionData.history.length > 0
            ? currentSessionData.history[0].timestamp
            : new Date().toISOString(),
        message_count: currentSessionData.history
          ? currentSessionData.history.length
          : 0,
        last_message:
          currentSessionData.history && currentSessionData.history.length > 0
            ? currentSessionData.history[currentSessionData.history.length - 1]
                .question
            : "Нет сообщений",
      };

      const realSessions = [currentSession];

      setSessions(realSessions);
    } catch (error) {
      console.error("Error loading sessions:", error);
      setSessions([
        {
          session_id: currentSessionId,
          start_time: new Date().toISOString(),
          message_count: 0,
          last_message: "Нет сообщений",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("ru-RU", {
        day: "numeric",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "Неизвестная дата";
    }
  };

  const exportChatHistory = async (sessionId) => {
    try {
      const response = await chatAPI.getChatHistory(sessionId);
      const historyData = response.data;

      const session = sessions.find((s) => s.session_id === sessionId);
      const exportData = {
        session_id: sessionId,
        export_date: new Date().toISOString(),
        message_count: session?.message_count || 0,
        messages: historyData.history || [],
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `transneft_chat_history_${sessionId.slice(0, 8)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error exporting chat history:", error);
      alert("Ошибка при экспорте истории чата");
    }
  };

  const getTotalMessages = () => {
    return sessions.reduce(
      (total, session) => total + session.message_count,
      0
    );
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
        <button
          onClick={() => {
            clearChat();
            loadSessions();
          }}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
        >
          🆕 Новая сессия
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Всего сессий</h3>
          <p className="text-2xl font-bold text-gray-900">{sessions.length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Всего сообщений</h3>
          <p className="text-2xl font-bold text-gray-900">
            {getTotalMessages()}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Текущая сессия</h3>
          <p className="text-lg font-semibold text-blue-600">
            {currentSessionId?.slice(0, 8)}...
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Сессии чата</h2>
          {sessions.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>Нет сохраненных сессий</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.session_id}
                className={`bg-white p-4 rounded-lg border border-gray-200 cursor-pointer transition-all hover:shadow-md ${
                  selectedSession === session.session_id
                    ? "ring-2 ring-blue-500"
                    : ""
                }`}
                onClick={() => loadSessionMessages(session.session_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">
                      Сессия: {currentSessionId}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                      {formatDate(session.start_time)}
                    </p>
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {session.last_message}
                    </p>
                  </div>
                  <div className="text-right ml-4">
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
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded text-xs font-medium transition-colors"
                  >
                    Просмотреть
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      exportChatHistory(session.session_id);
                    }}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded text-xs font-medium transition-colors"
                  >
                    Экспорт
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
        /
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              {selectedSession
                ? `Сообщения сессии ${selectedSession.slice(0, 8)}...`
                : "Выберите сессию"}
            </h2>
            {selectedSession && (
              <button
                onClick={() => exportChatHistory(selectedSession)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors"
              >
                Экспорт
              </button>
            )}
          </div>

          {selectedSession ? (
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {messagesLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                </div>
              ) : sessionMessages.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>Нет сообщений в этой сессии</p>
                </div>
              ) : (
                sessionMessages.map((message, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg ${
                      message.role === "user"
                        ? "bg-blue-50 border border-blue-200"
                        : "bg-gray-50 border border-gray-200"
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          message.role === "user"
                            ? "bg-blue-100 text-blue-600"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {message.role === "user" ? "👤" : "🤖"}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <div className="text-sm font-medium text-gray-900">
                            {message.role === "user"
                              ? "Вы"
                              : "Ассистент Транснефть"}
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatDate(message.timestamp)}
                          </div>
                        </div>
                        <div className="text-sm text-gray-700 mt-2 whitespace-pre-wrap">
                          {message.content}
                        </div>
                        {message.role === "assistant" &&
                          message.sources &&
                          message.sources.length > 0 && (
                            <div className="mt-2 text-xs text-gray-500">
                              📚 Источники: {message.sources.length}
                            </div>
                          )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500 bg-white rounded-lg border border-gray-200">
              <div className="text-4xl mb-4">📋</div>
              <p className="text-lg font-medium">Выберите сессию</p>
              <p className="text-sm mt-2">для просмотра истории сообщений</p>
            </div>
          )}
        </div>
      </div>

      {/* Информация о данных */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <div className="text-blue-600 text-lg mr-2">💡</div>
          <div>
            <h3 className="text-blue-800 font-medium">Информация о данных</h3>
            <p className="text-blue-700 text-sm mt-1">
              Все сообщения сохраняются в базе данных. Для получения полной
              истории всех сессий необходим дополнительный endpoint на сервере.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default History;
