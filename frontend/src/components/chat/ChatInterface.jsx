// src/components/chat/ChatInterface.jsx
import React, { useState, useRef, useEffect } from "react";
import Message from "./Message";
import QuickActions from "./QuickActions";
import SourceDocuments from "./SourceDocuments";
import { useChat } from "../../hooks/useChat";

const ChatInterface = () => {
  const { messages, sendMessage, isLoading, systemReady } = useChat();

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
    <div className="flex flex-col h-full">
      {/* Quick Actions */}
      <QuickActions onActionClick={handleQuickAction} />

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-12">
            <p className="text-lg">
              💡 Задайте первый вопрос о ПАО "Транснефть"
            </p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index}>
              <Message message={message} isUser={message.role === "user"} />
              {message.sources && message.sources.length > 0 && (
                <SourceDocuments sources={message.sources} />
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-6">
        <form onSubmit={handleSubmit} className="flex space-x-4">
          <div className="flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Например: Каков размер уставного капитала Транснефти? Или: Когда компания была основана?"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows="3"
              disabled={isLoading || !systemReady}
            />
          </div>
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading || !systemReady}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed self-end"
          >
            {isLoading ? (
              <div className="flex items-center">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Поиск...
              </div>
            ) : (
              "🚀 Отправить"
            )}
          </button>
        </form>

        {!systemReady && (
          <div className="mt-2 text-sm text-orange-600">
            ⚠️ Система инициализируется...
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
