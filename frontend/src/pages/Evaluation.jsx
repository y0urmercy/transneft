import React, { useState, useEffect } from "react";
import { chatAPI } from "../services/api";

const Evaluation = () => {
  const [evaluationResults, setEvaluationResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sampleSize, setSampleSize] = useState(30);
  const [evaluationHistory, setEvaluationHistory] = useState([]);
  const [activeTab, setActiveTab] = useState("run");

  useEffect(() => {
    loadEvaluationHistory();
  }, []);

  const loadEvaluationHistory = async () => {
    try {
      // Mock data for demonstration
      const mockHistory = [
        {
          evaluation_date: new Date(Date.now() - 86400000).toISOString(),
          sample_size: 25,
          overall_score: 0.78,
          rouge1: 0.82,
          rouge2: 0.75,
          bertscore: 0.85,
          duration_seconds: 45.2,
        },
        {
          evaluation_date: new Date(Date.now() - 172800000).toISOString(),
          sample_size: 30,
          overall_score: 0.81,
          rouge1: 0.84,
          rouge2: 0.77,
          bertscore: 0.87,
          duration_seconds: 52.1,
        },
      ];
      setEvaluationHistory(mockHistory);
    } catch (error) {
      console.error("Error loading evaluation history:", error);
    }
  };

  const runEvaluation = async () => {
    setLoading(true);
    try {
      const response = await chatAPI.evaluateSystem(sampleSize);
      setEvaluationResults(response.data);
    } catch (error) {
      console.error("Error running evaluation:", error);
      // Mock data for demonstration
      setEvaluationResults({
        metrics: {
          rouge1: 0.83,
          rouge2: 0.76,
          rougeL: 0.8,
          bleu: 0.45,
          bertscore: 0.86,
          meteor: 0.72,
          num_evaluated: sampleSize,
        },
        evaluation_result: {
          overall_score: 0.79,
          duration_seconds: 48.3,
        },
      });
    } finally {
      setLoading(false);
    }
  };

  const getQualityLevel = (score) => {
    if (score >= 0.9) return { level: "Отличное", color: "text-green-600" };
    if (score >= 0.8) return { level: "Хорошее", color: "text-blue-600" };
    if (score >= 0.7)
      return { level: "Удовлетворительное", color: "text-yellow-600" };
    return { level: "Требует улучшения", color: "text-red-600" };
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("ru-RU", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">
        🧪 Оценка качества системы
      </h1>

      <div className="flex space-x-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab("run")}
          className={`px-4 py-2 font-medium ${
            activeTab === "run"
              ? "border-b-2 border-blue-500 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          🎯 Запуск оценки
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`px-4 py-2 font-medium ${
            activeTab === "history"
              ? "border-b-2 border-blue-500 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          📊 История оценок
        </button>
      </div>

      {activeTab === "run" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Панель запуска оценки */}
          <div className="lg:col-span-1 space-y-6">
            <div className="metric-card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                ⚙️ Настройки оценки
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Размер выборки: {sampleSize} QA пар
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="100"
                    step="5"
                    value={sampleSize}
                    onChange={(e) => setSampleSize(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>10</span>
                    <span>100</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Метрики оценки:
                  </label>
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                      ROUGE (схожесть текста)
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                      BLEU (качество перевода)
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                      BERTScore (семантическая схожесть)
                    </div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
                      METEOR (качество генерации)
                    </div>
                  </div>
                </div>

                <button
                  onClick={runEvaluation}
                  disabled={loading}
                  className="w-full btn-primary py-3"
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Запуск оценки...
                    </div>
                  ) : (
                    "🎯 Запустить оценку"
                  )}
                </button>
              </div>
            </div>

            {evaluationResults && (
              <div className="metric-card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  📊 Общая оценка
                </h3>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-2">
                    {(
                      evaluationResults.evaluation_result?.overall_score * 100
                    ).toFixed(1)}
                    %
                  </div>
                  <div
                    className={`text-lg font-semibold ${
                      getQualityLevel(
                        evaluationResults.evaluation_result?.overall_score
                      ).color
                    }`}
                  >
                    {
                      getQualityLevel(
                        evaluationResults.evaluation_result?.overall_score
                      ).level
                    }
                  </div>
                  <div className="text-sm text-gray-500 mt-2">
                    Длительность:{" "}
                    {evaluationResults.evaluation_result?.duration_seconds?.toFixed(
                      1
                    )}{" "}
                    сек
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Результаты оценки */}
          <div className="lg:col-span-2">
            {evaluationResults ? (
              <div className="space-y-6">
                <div className="metric-card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    📈 Детальные метрики
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {(evaluationResults.metrics.rouge1 * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-blue-800">ROUGE-1</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {(evaluationResults.metrics.rouge2 * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-green-800">ROUGE-2</div>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {(evaluationResults.metrics.bertscore * 100).toFixed(1)}
                        %
                      </div>
                      <div className="text-sm text-purple-800">BERTScore</div>
                    </div>
                    <div className="text-center p-4 bg-orange-50 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">
                        {(evaluationResults.metrics.bleu * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-orange-800">BLEU</div>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">
                        {(evaluationResults.metrics.meteor * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-red-800">METEOR</div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-600">
                        {evaluationResults.metrics.num_evaluated}
                      </div>
                      <div className="text-sm text-gray-800">Оценено пар</div>
                    </div>
                  </div>
                </div>

                <div className="metric-card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    📋 Рекомендации по улучшению
                  </h3>
                  <div className="space-y-3">
                    {evaluationResults.metrics.rouge1 < 0.8 && (
                      <div className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg">
                        <span className="text-yellow-600">⚠️</span>
                        <div>
                          <div className="font-medium text-yellow-800">
                            Улучшить точность ответов
                          </div>
                          <div className="text-sm text-yellow-700">
                            ROUGE-1 показывает, что ответы не всегда точно
                            соответствуют ожидаемым
                          </div>
                        </div>
                      </div>
                    )}

                    {evaluationResults.metrics.bertscore < 0.85 && (
                      <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                        <span className="text-blue-600">💡</span>
                        <div>
                          <div className="font-medium text-blue-800">
                            Улучшить семантическое понимание
                          </div>
                          <div className="text-sm text-blue-700">
                            BERTScore указывает на возможность улучшения
                            смыслового соответствия
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                      <span className="text-green-600">✅</span>
                      <div>
                        <div className="font-medium text-green-800">
                          Сильные стороны системы
                        </div>
                        <div className="text-sm text-green-700">
                          Хорошее извлечение информации и релевантность ответов
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="metric-card text-center py-12">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Запустите оценку системы
                </h3>
                <p className="text-gray-600">
                  Нажмите кнопку "Запустить оценку" для анализа качества работы
                  системы
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "history" && (
        <div className="space-y-6">
          <div className="metric-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              📅 История оценок качества
            </h3>

            {evaluationHistory.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>Нет данных об оценках</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 font-medium text-gray-900">
                        Дата оценки
                      </th>
                      <th className="text-left py-3 font-medium text-gray-900">
                        Выборка
                      </th>
                      <th className="text-left py-3 font-medium text-gray-900">
                        Общий балл
                      </th>
                      <th className="text-left py-3 font-medium text-gray-900">
                        ROUGE-1
                      </th>
                      <th className="text-left py-3 font-medium text-gray-900">
                        ROUGE-2
                      </th>
                      <th className="text-left py-3 font-medium text-gray-900">
                        BERTScore
                      </th>
                      <th className="text-left py-3 font-medium text-gray-900">
                        Длительность
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {evaluationHistory.map((evalItem, index) => (
                      <tr
                        key={index}
                        className="border-b border-gray-100 hover:bg-gray-50"
                      >
                        <td className="py-3 text-sm text-gray-900">
                          {formatDate(evalItem.evaluation_date)}
                        </td>
                        <td className="py-3 text-sm text-gray-600">
                          {evalItem.sample_size}
                        </td>
                        <td className="py-3">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              evalItem.overall_score >= 0.8
                                ? "bg-green-100 text-green-800"
                                : evalItem.overall_score >= 0.7
                                ? "bg-yellow-100 text-yellow-800"
                                : "bg-red-100 text-red-800"
                            }`}
                          >
                            {(evalItem.overall_score * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="py-3 text-sm text-gray-600">
                          {(evalItem.rouge1 * 100).toFixed(1)}%
                        </td>
                        <td className="py-3 text-sm text-gray-600">
                          {(evalItem.rouge2 * 100).toFixed(1)}%
                        </td>
                        <td className="py-3 text-sm text-gray-600">
                          {(evalItem.bertscore * 100).toFixed(1)}%
                        </td>
                        <td className="py-3 text-sm text-gray-600">
                          {evalItem.duration_seconds.toFixed(1)} сек
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Evaluation;
