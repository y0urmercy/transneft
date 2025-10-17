import React, { useState, useRef, useEffect } from "react";
import { useChat } from "../../hooks/useChat";
import VoiceInput from "../voice/VoiceInput";
import VoiceOutput from "../voice/VoiceOutput";
import { useSpeech } from "../../hooks/useSpeech";

const ChatInterface = () => {
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading) {
      await sendMessage(inputMessage.trim());
      setInputMessage("");
    }
  };

  const handleVoiceTranscript = (transcript) => {
    setInputMessage(transcript);
    if (transcript.trim()) {
      handleSendVoiceMessage(transcript);
    }
  };

  const handleSendVoiceMessage = async (text) => {
    await sendMessage(text.trim());
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

  const getLastAssistantMessage = () => {
    const assistantMessages = messages.filter(
      (msg) => msg.role === "assistant"
    );
    return assistantMessages.length > 0
      ? assistantMessages[assistantMessages.length - 1].content
      : "";
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2 className="chat-title">Голосовой помощник ПАО "Транснефть"</h2>
        <div className="status-indicator">
          {systemReady ? (
            <span className="status-ready">
              <div className="status-dot ready"></div>
              Система готова
            </span>
          ) : (
            <span className="status-initializing">
              <div className="status-dot initializing"></div>
              Система инициализируется...
            </span>
          )}
        </div>
      </div>

      <div className="chat-main">
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <div className="welcome-icon">🎤</div>
              <p className="welcome-title">
                Добро пожаловать в голосовой помощник ПАО "Транснефть"
              </p>
              <p className="welcome-subtitle">
                Задайте вопрос голосом или текстом о компании, её деятельности,
                финансах или проектах
              </p>
              <div className="voice-input-wrapper">
                <VoiceInput
                  onTranscript={handleVoiceTranscript}
                  onStart={handleVoiceInputStart}
                  onEnd={handleVoiceInputEnd}
                />
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`message ${message.role}`}>
                <div className="message-content">
                  <div className="message-avatar">
                    {message.role === "user" ? "👤" : "🤖"}
                  </div>
                  <div className="message-body">
                    <div className="message-header">
                      <div className="message-sender">
                        {message.role === "user" ? "Вы" : "Помощник Транснефть"}
                      </div>
                      {message.role === "assistant" && (
                        <VoiceOutput
                          text={message.content}
                          onSpeak={() => handleSpeakResponse(message.content)}
                          onStop={handleStopSpeaking}
                          isSpeaking={isSpeaking}
                        />
                      )}
                    </div>
                    <div className="message-text">{message.content}</div>
                    <div className="message-time">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} className="messages-end" />
        </div>

        <div className="input-section">
          {error && (
            <div className="error-message">
              <p>⚠️ {error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="input-form">
            <div className="input-wrapper">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Например: Каков размер уставного капитала Транснефти? Или: Когда компания была основана?"
                className="text-input"
                rows="3"
                disabled={isLoading}
              />
              <div className="voice-input-container">
                <VoiceInput
                  onTranscript={handleVoiceTranscript}
                  onStart={handleVoiceInputStart}
                  onEnd={handleVoiceInputEnd}
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={!inputMessage.trim() || isLoading}
              className="send-button"
            >
              {isLoading ? (
                <div className="loading-indicator">
                  <div className="loading-spinner"></div>
                  Поиск...
                </div>
              ) : (
                "Отправить"
              )}
            </button>
          </form>

          <div className="input-footer">
            <div className="system-status">
              {!systemReady ? (
                <span className="status-warning">
                  Система инициализируется...
                </span>
              ) : (
                <span className="status-success">Система готова к работе</span>
              )}
            </div>

            {messages.length > 0 && (
              <span className="message-count">
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
