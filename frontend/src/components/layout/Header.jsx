// src/components/layout/Header.jsx
import React, { useState } from "react";

const Header = ({ onMenuClick, currentPage }) => {
  const [showSettings, setShowSettings] = useState(false);

  const pageTitles = {
    chat: "💬 Чат-бот",
    history: "📊 История",
    analytics: "📈 Аналитика",
    evaluation: "🧪 Оценка качества",
    admin: "🔧 Администрирование",
  };

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md text-gray-600 hover:bg-gray-100 mr-4"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
          <h1 className="text-2xl font-bold text-gray-800">
            {pageTitles[currentPage]}
          </h1>
        </div>

        <div className="flex items-center space-x-4">
          {/* Кнопка настроек */}
          <div className="relative">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 rounded-md text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </button>

            {/* Dropdown меню */}
            {showSettings && (
              <div className="absolute right-0 mt-2 w-64 bg-white rounded-md shadow-lg border border-gray-200 py-2 z-50">
                <button
                  onClick={() => {
                    setShowSettings(false);
                    // Переход на страницу аналитики
                    window.location.hash = "#analytics";
                  }}
                  className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                >
                  📊 Аналитика системы
                </button>
                <button
                  onClick={() => {
                    setShowSettings(false);
                    window.location.hash = "#evaluation";
                  }}
                  className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                >
                  🧪 Оценка качества
                </button>
                <button
                  onClick={() => {
                    setShowSettings(false);
                    window.location.hash = "#admin";
                  }}
                  className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                >
                  🔧 Администрирование
                </button>
                <div className="border-t border-gray-200 my-1"></div>
                <button className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left">
                  ⚙️ Настройки системы
                </button>
                <button className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left">
                  🆘 Помощь
                </button>
              </div>
            )}
          </div>

          {/* Индикатор сессии */}
          <div className="text-sm text-gray-500 hidden md:block">
            Сессия: {Math.random().toString(36).substr(2, 8)}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
