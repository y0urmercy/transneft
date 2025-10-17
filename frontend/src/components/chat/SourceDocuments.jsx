import React, { useState } from "react";

const SourceDocuments = ({ sources }) => {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-2 animate-slide-up">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        {!expanded ? (
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-blue-900 flex items-center">
              <span className="mr-2">📚</span>
              Источники информации
            </h4>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">
                {sources.length} источников
              </span>
              <button
                onClick={() => setExpanded(true)}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center"
              >
                Показать источники
                <span className="ml-1">↓</span>
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-blue-900 flex items-center">
                <span className="mr-2">📚</span>
                Источники информации
              </h4>
              <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">
                {sources.length} источников
              </span>
            </div>

            <div className="space-y-2">
              {sources.map((source, index) => (
                <div key={index} className="text-sm text-blue-800">
                  <div className="font-medium mb-1">
                    Источник #{index + 1}
                    {source.score && (
                      <span className="text-blue-600 ml-2">
                        (релевантность: {(source.score * 100).toFixed(1)}%)
                      </span>
                    )}
                  </div>
                  <div className="text-blue-700 bg-white p-2 rounded border border-blue-100">
                    {source.content}
                  </div>
                  {source.sections && source.sections.length > 0 && (
                    <div className="text-xs text-blue-600 mt-1">
                      Разделы: {source.sections.join(", ")}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <button
              onClick={() => setExpanded(false)}
              className="mt-3 text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center"
            >
              Свернуть
              <span className="ml-1">↑</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SourceDocuments;
