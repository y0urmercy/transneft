// src/components/common/Avatar.jsx
import React, { useEffect, useRef } from "react";

const Avatar = ({ state = "idle", onStateChange }) => {
  const avatarRef = useRef(null);
  const timeoutRef = useRef(null);

  const animations = {
    welcome: "/avatars/welcome.gif",
    idle: "/avatars/idle.gif",
    engagement: "/avatars/engagement.gif",
    goodbye: "/avatars/goodbye.gif",
  };

  useEffect(() => {
    // Автоматическое переключение анимаций
    const scheduleAnimation = () => {
      clearTimeout(timeoutRef.current);

      switch (state) {
        case "welcome":
          timeoutRef.current = setTimeout(() => {
            onStateChange("idle");
          }, 3000);
          break;

        case "engagement":
          timeoutRef.current = setTimeout(() => {
            onStateChange("idle");
          }, 5000);
          break;

        case "goodbye":
          timeoutRef.current = setTimeout(() => {
            onStateChange("idle");
          }, 2000);
          break;

        case "idle":
          // Случайные микро-анимации в режиме ожидания
          timeoutRef.current = setTimeout(() => {
            // Случайное событие для вовлечения
            if (Math.random() > 0.7) {
              onStateChange("engagement");
            }
          }, 15000);
          break;
      }
    };

    scheduleAnimation();

    return () => clearTimeout(timeoutRef.current);
  }, [state, onStateChange]);

  return (
    <div className="relative w-64 h-64">
      <img
        ref={avatarRef}
        src={animations[state] || animations.idle}
        alt="Аватар помощника"
        className="w-full h-full object-contain"
        onLoad={() => {
          // Триггер приветствия при первой загрузке
          if (state === "idle") {
            onStateChange("welcome");
          }
        }}
      />
    </div>
  );
};

export default Avatar;
