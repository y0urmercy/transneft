import React, { useState, useRef, useEffect } from "react";
import Message from "../components/chat/Message";
import QuickActions from "../components/chat/QuickActions";
import SourceDocuments from "../components/chat/SourceDocuments";
import { useChat } from "../hooks/useChat";

const Chat = () => {
  const { messages, sendMessage, isLoading, systemReady, error } = useChat();

  const [inputMessage, setInputMessage] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading && systemReady) {
      sendMessage(inputMessage.trim());
      setInputMessage("");
    }
  };

  const handleQuickAction = (question) => {
    sendMessage(question);
  };

  return (
    <div className="flex flex-col h-full bg-white">
      <QuickActions onActionClick={handleQuickAction} />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-12">
            <div className="text-6xl mb-4">💡</div>
            <p className="text-lg font-medium mb-2">
              Добро пожаловать в экспертную систему ПАО "Транснефть"
            </p>
            <p className="text-sm">
              Задайте вопрос или выберите один из примеров ниже
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id || message.timestamp}>
              <Message message={message} isUser={message.role === "user"} />
              {message.sources && message.sources.length > 0 && (
                <SourceDocuments sources={message.sources} />
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="mx-6 mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center text-red-700">
            <span className="text-lg mr-2">⚠️</span>
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      <div className="border-t border-gray-200 p-6 bg-white">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <div className="flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Например: Каков размер уставного капитала Транснефти? Или: Когда компания была основана?"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-colors"
              rows="3"
              disabled={isLoading || !systemReady}
            />
          </div>
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading || !systemReady}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed self-end transition-colors font-medium"
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

        {!systemReady && (
          <div className="mt-2 text-sm text-orange-600 flex items-center">
            <div className="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
            Система инициализируется...
          </div>
        )}
      </div>
    </div>
  );
};

export default Chat;
