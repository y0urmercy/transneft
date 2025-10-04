// src/components/common/Avatar.jsx
import React, { useEffect, useRef, useState } from "react";

const Avatar = ({
  state = "idle",
  onStateChange,
  chatInterfaceRef, // Референс на компонент ChatInterface для отслеживания ввода текста
}) => {
  const avatarRef = useRef(null);
  const timeoutRef = useRef(null);
  const inputCheckRef = useRef(null);
  const [hasWelcomed, setHasWelcomed] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  const animations = {
    welcome: "/public/avatars/welcome.gif",
    idle: "/public/avatars/idle.gif",
    engagement: "/public/avatars/engagement.gif",
    goodbye: "/public/avatars/goodbye.gif",
    typing: "/public/avatars/typing.gif", // Новая анимация для набора текста
  };

  // Отслеживание ввода текста в ChatInterface
  useEffect(() => {
    if (!chatInterfaceRef?.current) return;

    const checkUserInput = () => {
      try {
        // Получаем элементы ввода из ChatInterface
        const inputElement = chatInterfaceRef.current?.querySelector?.(
          'input[type="text"], textarea'
        );
        const messageContainer = chatInterfaceRef.current?.querySelector?.(
          ".messages, .chat-messages"
        );

        let userText = "";

        // Получаем текст из поля ввода
        if (inputElement) {
          userText = inputElement.value.toLowerCase().trim();
        }

        // Ищем последние сообщения пользователя
        if (messageContainer) {
          const userMessages = messageContainer.querySelectorAll(
            ".user-message, .message-user"
          );
          if (userMessages.length > 0) {
            const lastUserMessage = userMessages[userMessages.length - 1];
            userText = lastUserMessage.textContent.toLowerCase().trim();
          }
        }

        // Проверяем на прощание
        const goodbyeKeywords = [
          "до свидания",
          "пока",
          "завершить",
          "закончить",
          "выход",
          "bye",
          "goodbye",
        ];
        const isGoodbye = goodbyeKeywords.some((keyword) =>
          userText.includes(keyword)
        );

        if (isGoodbye && state !== "goodbye") {
          onStateChange("goodbye");
          return;
        }

        // Проверяем, печатает ли пользователь
        const currentlyTyping = inputElement && inputElement.value.length > 0;
        if (currentlyTyping !== isTyping) {
          setIsTyping(currentlyTyping);
          if (currentlyTyping && state !== "typing" && state !== "goodbye") {
            onStateChange("typing");
          } else if (!currentlyTyping && state === "typing") {
            onStateChange("idle");
          }
        }
      } catch (error) {
        console.error("Error checking user input:", error);
      }
    };

    // Проверяем ввод каждые 500ms
    inputCheckRef.current = setInterval(checkUserInput, 500);

    return () => {
      if (inputCheckRef.current) {
        clearInterval(inputCheckRef.current);
      }
    };
  }, [chatInterfaceRef, state, isTyping, onStateChange]);

  // Автоматическое переключение анимаций
  useEffect(() => {
    const scheduleAnimation = () => {
      clearTimeout(timeoutRef.current);

      switch (state) {
        case "welcome":
          timeoutRef.current = setTimeout(() => {
            onStateChange("idle");
          }, 1500);
          break;

        case "engagement":
          timeoutRef.current = setTimeout(() => {
            onStateChange("idle");
          }, 1500);
          break;

        case "typing":
          // Анимация typing продолжается пока пользователь печатает
          // Переключение обратно происходит в эффекте отслеживания ввода
          break;

        case "goodbye":
          timeoutRef.current = setTimeout(() => {
            onStateChange("idle");
            setHasWelcomed(false);
          }, 1500);
          break;

        case "idle":
          // Случайные микро-анимации в режиме ожидания
          if (!isTyping) {
            timeoutRef.current = setTimeout(() => {
              if (Math.random() > 0.7) {
                onStateChange("engagement");
              }
            }, 5000 + Math.random() * 10000);
          }
          break;
      }
    };

    scheduleAnimation();

    return () => clearTimeout(timeoutRef.current);
  }, [state, onStateChange, isTyping]);

  // Расширенное приветствие на первые 7 секунд
  useEffect(() => {
    if (state === "idle" && !hasWelcomed) {
      const welcomeTimer = setTimeout(() => {
        onStateChange("welcome");
        setHasWelcomed(true);

        // После приветствия показываем дополнительные анимации вовлечения
        const engagementTimer = setTimeout(() => {
          if (state === "idle") {
            onStateChange("engagement");
          }
        }, 3000);

        return () => clearTimeout(engagementTimer);
      }, 1000);

      return () => clearTimeout(welcomeTimer);
    }
  }, [state, hasWelcomed, onStateChange]);

  // Обработчик активности пользователя (прерывание анимаций)
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

  // Определяем текущую анимацию с учетом состояния набора текста
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
          console.error(`Failed to load animation: ${getCurrentAnimation()}`);
          e.target.src = animations.idle;
        }}
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
