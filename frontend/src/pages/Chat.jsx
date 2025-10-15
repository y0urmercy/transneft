import React, { useState, useRef, useEffect } from "react";
import Message from "../components/chat/Message";
import QuickActions from "../components/chat/QuickActions";
import SourceDocuments from "../components/chat/SourceDocuments";
import VoiceInput from "../components/voice/VoiceInput";
import VoiceOutput from "../components/voice/VoiceOutput";
import { useChat } from "../hooks/useChat";
import { useSpeech } from "../hooks/useSpeech";

const Chat = () => {
  const { messages, sendMessage, isLoading, systemReady, error } = useChat();
  const { speak, stop, isSpeaking } = useSpeech();

  const [inputMessage, setInputMessage] = useState("");
  const [isVoiceInputActive, setIsVoiceInputActive] = useState(false);
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

  const handleVoiceTranscript = (transcript) => {
    setInputMessage(transcript);
    if (transcript.trim() && systemReady && !isLoading) {
      handleSendVoiceMessage(transcript);
    }
  };

  const handleSendVoiceMessage = async (text) => {
    sendMessage(text.trim());
    setInputMessage("");
  };

  const handleVoiceInputStart = () => {
    setIsVoiceInputActive(true);
  };

  const handleVoiceInputEnd = () => {
    setIsVoiceInputActive(false);
  };

  const handleSpeakResponse = (text) => {
    if (text) {
      speak(text);
    }
  };

  const handleStopSpeaking = () => {
    stop();
  };

  return (
    <div className="flex flex-col h-full bg-white">
      <QuickActions onActionClick={handleQuickAction} />

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-12">
            <div className="text-6xl mb-4">🎤</div>
            <p className="text-lg font-medium mb-2">
              Добро пожаловать в голосовой помощник ПАО "Транснефть"
            </p>
            <p className="text-sm mb-6">
              Задайте вопрос голосом или текстом, или выберите один из примеров
              ниже
            </p>
            <div className="flex justify-center">
              <VoiceInput
                onTranscript={handleVoiceTranscript}
                onStart={handleVoiceInputStart}
                onEnd={handleVoiceInputEnd}
              />
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id || message.timestamp}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <Message message={message} isUser={message.role === "user"} />
                </div>
                {message.role === "assistant" && message.content && (
                  <div className="ml-4 mt-2">
                    <VoiceOutput
                      text={message.content}
                      onSpeak={() => handleSpeakResponse(message.content)}
                      onStop={handleStopSpeaking}
                      isSpeaking={isSpeaking}
                    />
                  </div>
                )}
              </div>
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
          <div className="flex-1 relative">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Например: Каков размер уставного капитала Транснефти? Или: Когда компания была основана?"
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-colors"
              rows="3"
              disabled={isLoading || !systemReady}
            />
            <div className="absolute right-3 bottom-3">
              <VoiceInput
                onTranscript={handleVoiceTranscript}
                onStart={handleVoiceInputStart}
                onEnd={handleVoiceInputEnd}
              />
            </div>
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

        <div className="mt-3 flex items-center justify-between text-sm">
          <div>
            {!systemReady ? (
              <div className="text-orange-600 flex items-center">
                <div className="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
                Система инициализируется...
              </div>
            ) : (
              <div className="text-green-600 flex items-center">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                Система готова
              </div>
            )}
          </div>

          {isVoiceInputActive && (
            <div className="text-blue-600 flex items-center">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse mr-2"></div>
              Слушаю...
            </div>
          )}

          {messages.length > 0 && (
            <span className="text-gray-500">
              {messages.filter((m) => m.role === "user").length} сообщений
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default Chat;
