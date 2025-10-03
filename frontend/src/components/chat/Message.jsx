import React from "react";

const Message = ({ message, isUser }) => {
  const formatTime = (timestamp) => {
    if (!timestamp) return "";
    const date = new Date(timestamp);
    return date.toLocaleTimeString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      } animate-fade-in`}
    >
      <div
        className={`max-w-3xl rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-blue-600 text-white rounded-br-none"
            : "bg-gray-100 text-gray-800 rounded-bl-none"
        }`}
      >
        <div className="whitespace-pre-wrap break-words">{message.content}</div>
        <div
          className={`text-xs mt-2 ${
            isUser ? "text-blue-100" : "text-gray-500"
          }`}
        >
          {formatTime(message.timestamp)}
          {message.confidence && !isUser && (
            <span className="ml-2">
              • Уверенность: {(message.confidence * 100).toFixed(1)}%
            </span>
          )}
          {message.isError && <span className="ml-2">• Ошибка</span>}
        </div>
      </div>
    </div>
  );
};

export default Message;
