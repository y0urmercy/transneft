import React from "react";

const QuickActions = ({ onActionClick }) => {
  const quickQuestions = [
    {
      question: "Каков размер уставного капитала Транснефти?",
      emoji: "💰",
    },
    {
      question: "Когда компания была основана?",
      emoji: "📅",
    },
    {
      question: "Основные направления деятельности компании?",
      emoji: "🎯",
    },
    {
      question: "География присутствия Транснефти?",
      emoji: "🌍",
    },
  ];

  return (
    <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
      <h3 className="text-sm font-medium text-gray-700 mb-3">
        Быстрые вопросы:
      </h3>
      <div className="flex flex-wrap gap-2">
        {quickQuestions.map((item, index) => (
          <button
            key={index}
            onClick={() => onActionClick(item.question)}
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-full text-sm text-gray-700 bg-white hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
          >
            <span className="mr-2">{item.emoji}</span>
            {item.question}
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuickActions;
