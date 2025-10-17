import React, { useState } from "react";

const Header = ({ onMenuClick, currentPage }) => {
  const [showSettings, setShowSettings] = useState(false);

  const pageTitles = {
    chat: "Чат-бот",
    history: "История",
    evaluation: "Оценка качества",
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

        <div className="flex items-center space-x-4"></div>
      </div>
    </header>
  );
};

export default Header;
