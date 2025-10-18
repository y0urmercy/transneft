// src/components/common/Avatar.jsx
import React, { useEffect, useRef, useState } from "react";
import { useChat } from "../../hooks/useChat";

const Avatar = ({ state = "idle", onStateChange }) => {
  const avatarRef = useRef(null);
  const timeoutRef = useRef(null);
  const [hasWelcomed, setHasWelcomed] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [hasSaidWelcome, setHasSaidWelcome] = useState(false);
  const [hasSaidGoodbye, setHasSaidGoodbye] = useState(false);
  const [lastProcessedMessageId, setLastProcessedMessageId] = useState(null); // Отслеживаем обработанные сообщения

  // Получаем сообщения из хука useChat
  const { messages } = useChat();

  const animations = {
    welcome: "/avatars/welcome.gif",
    idle: "/avatars/idle.gif",
    engagement: "/avatars/engagement.gif",
    goodbye: "/avatars/goodbye.gif",
    typing: "/avatars/typing.gif",
  };

  const log = (message, type = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    const logMessage = `[Avatar] ${message}`;
    console.log(`[${type.toUpperCase()}] ${logMessage}`);
  };

  useEffect(() => {
    if (hasSaidWelcome) {
      return;
    }
    if (hasSaidGoodbye) {
      return;
    }

    if (messages.length === 0) {
      return;
    }

    const lastMessage = messages[messages.length - 1];

    if (lastMessage.id === lastProcessedMessageId) {
      return;
    }

    if (lastMessage.role === "user") {
      const userText = lastMessage.content?.toLowerCase().trim() || "";

      const welcomeKeywords = [
        "привет",
        "здравствуй",
        "здравствуйте",
        "добрый день",
        "доброе утро",
        "добрый вечер",
        "приветствую",
        "хай",
        "hello",
        "hi",
        "hey",
        "здарова",
        "приветик",
        "салют",
        "доброго времени суток",
        "приветствую вас",
        "рад вас видеть",
        "начать",
        "старт",
        "помощь",
        "help",
        "меню",
        "что ты умеешь",
        "возможности",
        "Привет",
        "Здравствуй",
        "Здравствуйте",
        "Добрый день",
        "Доброе утро",
        "Добрый вечер",
        "Приветствую",
        "Хай",
        "Hello",
        "Hi",
        "Hey",
        "Здарова",
        "Приветик",
        "Салют",
        "Доброго времени суток",
        "Приветствую вас",
        "Рад вас видеть",
        "Начать",
        "Старт",
        "Помощь",
        "Help",
        "Меню",
        "Что ты умеешь",
        "Возможности",
        "ПРИВЕТ",
        "ЗДРАВСТВУЙТЕ",
        "ДОБРЫЙ ДЕНЬ",
        "HELLO",
        "HI",
      ];
      const goodbyeKeywords = [
        "до свидания",
        "пока",
        "завершить",
        "закончить",
        "выход",
        "bye",
        "goodbye",
        "спасибо пока",
        "всего хорошего",
        "до встречи",
        "прощай",
        "закончим",
        "закончили",
        "хватит",
        "стоп",
        "закрыть",
        "До свидания",
        "Пока",
        "Завершить",
        "Закончить",
        "Выход",
        "Bye",
        "Goodbye",
        "Спасибо пока",
        "Всего хорошего",
        "До встречи",
        "Прощай",
        "Закончим",
        "Закончили",
        "Хватит",
        "Стоп",
        "Закрыть",
        "ДО СВИДАНИЯ",
        "ПОКА",
        "ВЫХОД",
        "BYE",
        "GOODBYE",
        "СТОП",
      ];
      const foundKeywords_goodbye = goodbyeKeywords.filter((keyword) =>
        userText.includes(keyword)
      );

      const foundKeywords_hello = welcomeKeywords.filter((keyword) =>
        userText.includes(keyword)
      );

      if (foundKeywords_goodbye.length > 0) {
        if (state !== "goodbye") {
          setHasSaidGoodbye(true);
          onStateChange("goodbye");
        }
      }
      if (foundKeywords_hello.length > 0) {
        if (state !== "welcome") {
          setHasSaidWelcome(true);
          onStateChange("welcome");
        }
      }
    }

    setLastProcessedMessageId(lastMessage.id);
  }, [messages, state, onStateChange, hasSaidGoodbye, lastProcessedMessageId]);

  useEffect(() => {
    log(`Состояние изменилось на: ${state}`);

    const scheduleAnimation = () => {
      clearTimeout(timeoutRef.current);

      switch (state) {
        case "welcome":
          timeoutRef.current = setTimeout(() => {
            onStateChange("idle");
          }, 5400);
          break;

        case "engagement":
          timeoutRef.current = setTimeout(() => {
            onStateChange("idle");
          }, 3000);
          break;

        case "typing":
          break;

        case "goodbye":
          timeoutRef.current = setTimeout(() => {
            onStateChange("idle");
            setHasWelcomed(false);
          }, 6000);
          break;

        case "idle":
          if (!isTyping && !hasSaidGoodbye) {
            const delay = 5000 + Math.random() * 10000;
            timeoutRef.current = setTimeout(() => {
              if (Math.random() > 0.5) {
                onStateChange("engagement");
              }
            }, delay);
          }
          break;
      }
    };

    scheduleAnimation();

    return () => {
      clearTimeout(timeoutRef.current);
    };
  }, [state, onStateChange, isTyping, hasSaidGoodbye]);

  useEffect(() => {
    if (state === "idle" && !hasWelcomed) {
      const welcomeTimer = setTimeout(() => {
        onStateChange("welcome");
        setHasWelcomed(true);
      }, 1000);

      return () => clearTimeout(welcomeTimer);
    }
  }, [state, hasWelcomed, onStateChange]);

  useEffect(() => {
    const handleUserActivity = () => {
      if (state === "engagement" || state === "welcome") {
        clearTimeout(timeoutRef.current);
        onStateChange("idle");
      }
    };

    window.addEventListener("click", handleUserActivity);
    window.addEventListener("keydown", handleUserActivity);
    window.addEventListener("mousemove", handleUserActivity);

    return () => {
      window.removeEventListener("click", handleUserActivity);
      window.removeEventListener("keydown", handleUserActivity);
      window.removeEventListener("mousemove", handleUserActivity);
    };
  }, [state, onStateChange]);

  useEffect(() => {
    if (messages.length === 0 && lastProcessedMessageId !== null) {
      setLastProcessedMessageId(null);
      setHasSaidGoodbye(false);
    }
  }, [messages.length, lastProcessedMessageId]);

  const getCurrentAnimation = () => {
    if (state === "typing" && animations.typing) {
      return animations.typing;
    }
    return animations[state] || animations.idle;
  };

  return (
    <div className="relative w-64 h-64">
      <img
        ref={avatarRef}
        src={getCurrentAnimation()}
        alt="Аватар помощника"
        className="w-full h-full object-contain transition-opacity duration-300"
        onError={(e) => {
          e.target.src = animations.idle;
        }}
      />
      <img
        src="/avatars/logo.png"
        alt="Transneft_logo"
        className="absolute top-20 right-0 mr-24 w-5 h-5 object-contain"
      />
      {isTyping && (
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
          Печатает...
        </div>
      )}
    </div>
  );
};

export default Avatar;
