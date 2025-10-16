import React, { useState, useEffect } from "react";
import { chatAPI } from "../services/api";

const Evaluation = () => {
  const [evaluationResults, setEvaluationResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sampleSize, setSampleSize] = useState(10);
  const [evaluationHistory, setEvaluationHistory] = useState([]);
  const [activeTab, setActiveTab] = useState("run");
  const [error, setError] = useState(null);

  useEffect(() => {
    loadEvaluationHistory();
  }, []);

  const loadEvaluationHistory = async () => {
    setEvaluationHistory([]);
  };

  const runEvaluation = async () => {
    setLoading(true);
    setError(null);
    setEvaluationResults(null);

    try {
      console.log("Starting evaluation with sample size:", sampleSize);
      const response = await chatAPI.evaluateSystem(sampleSize, {
        timeout: 300000,
      });

      console.log("Raw response data:", response.data);

      const results = response.data;

      if (!results) {
        throw new Error("Пустой ответ от сервера");
      }

      if (results.status === "error") {
        throw new Error(results.message || "Ошибка при оценке системы");
      }

      let metrics = {};

      if (results.results) {
        metrics = { ...results.results };
      } else if (results.metrics) {
        metrics = { ...results.metrics };
      } else {
        metrics = {
          rouge1: results.rouge1,
          rouge2: results.rouge2,
          bertscore: results.bertscore || results.bertscore_f1,
          bleu: results.bleu,
          meteor: results.meteor,
          num_evaluated: results.num_evaluated || sampleSize,
        };
      }

      const filledMetrics = {
        rouge1: metrics.rouge1 || 0,
        rouge2: metrics.rouge2 || 0,
        bertscore: metrics.bertscore || metrics.bertscore_f1 || 0,
        bleu: metrics.bleu || 0,
        meteor: metrics.meteor || 0,
        num_evaluated: metrics.num_evaluated || sampleSize,
      };

      const overall_score =
        (filledMetrics.bertscore +
          filledMetrics.rouge1 +
          filledMetrics.rouge2) /
        3;

      const normalizedResults = {
        status: results.status || "success",
        message: results.message || "Evaluation completed",
        evaluation_result: {
          overall_score: overall_score,
          duration_seconds:
            results.duration_seconds || metrics.duration_seconds || 30,
        },
        metrics: filledMetrics,
      };

      console.log("Final normalized results:", normalizedResults);
      setEvaluationResults(normalizedResults);
    } catch (error) {
      console.error("Evaluation error details:", error);

      let errorMessage = "Неизвестная ошибка";
      if (error.response) {
        errorMessage =
          error.response.data?.detail ||
          error.response.data?.message ||
          `Ошибка сервера: ${error.response.status}`;
      } else if (error.request) {
        errorMessage = "Сервер не отвечает. Проверьте подключение.";
      } else {
        errorMessage = error.message || "Ошибка при выполнении запроса";
      }

      setError(errorMessage);
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
        Оценка качества системы
      </h1>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <div className="text-red-600 text-lg mr-2">❌</div>
            <div>
              <h3 className="text-red-800 font-medium">Ошибка оценки</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="flex space-x-2 border-b border-gray-200">
        <button
          onClick={() => setActiveTab("run")}
          className={`px-4 py-2 font-medium ${
            activeTab === "run"
              ? "border-b-2 border-blue-500 text-blue-600"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Запуск оценки
        </button>
      </div>

      {activeTab === "run" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                    min="5"
                    max="40"
                    step="5"
                    value={sampleSize}
                    onChange={(e) => setSampleSize(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>5</span>
                    <span>40</span>
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
                  </div>
                </div>

                <button
                  onClick={runEvaluation}
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-3 px-4 rounded-lg font-medium transition-colors"
                >
                  {loading ? (
                    <div className="flex items-center justify-center">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Запуск оценки...
                    </div>
                  ) : (
                    "Запустить оценку"
                  )}
                </button>

                <div className="text-xs text-gray-500 text-center">
                  Оценка может занять несколько минут
                </div>
              </div>
            </div>

            {evaluationResults && (
              <div className="metric-card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Общая оценка
                </h3>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600 mb-2">
                    {(
                      evaluationResults.evaluation_result?.overall_score * 100
                    ).toFixed(4)}
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
                      4
                    )}{" "}
                    сек
                  </div>
                  <div className="text-sm text-green-600 mt-1">
                    {evaluationResults.metrics.num_evaluated || 0} пар оценено
                  </div>
                </div>
              </div>
            )}
          </div>

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
                        {(
                          (evaluationResults.metrics.rouge1 || 0) * 100
                        ).toFixed(4)}
                        %
                      </div>
                      <div className="text-sm text-blue-800">ROUGE-1</div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">
                        {(
                          (evaluationResults.metrics.rouge2 || 0) * 100
                        ).toFixed(4)}
                        %
                      </div>
                      <div className="text-sm text-green-800">ROUGE-2</div>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {(
                          (evaluationResults.metrics.bertscore || 0) * 100
                        ).toFixed(4)}
                        %
                      </div>
                      <div className="text-sm text-purple-800">BERTScore</div>
                    </div>
                    <div className="text-center p-4 bg-orange-50 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">
                        {((evaluationResults.metrics.bleu || 0) * 100).toFixed(
                          4
                        )}
                        %
                      </div>
                      <div className="text-sm text-orange-800">BLEU</div>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">
                        {(
                          (evaluationResults.metrics.meteor || 0) * 100
                        ).toFixed(4)}
                        %
                      </div>
                      <div className="text-sm text-red-800">METEOR</div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-gray-600">
                        {evaluationResults.metrics.num_evaluated || 0}
                      </div>
                      <div className="text-sm text-gray-800">Оценено пар</div>
                    </div>
                  </div>
                </div>

                <div className="metric-card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Рекомендации по улучшению
                  </h3>
                  <div className="space-y-3">
                    {(evaluationResults.metrics.rouge1 || 0) < 0.8 && (
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

                    {(evaluationResults.metrics.bertscore || 0) < 0.85 && (
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

                    {(evaluationResults.metrics.rouge1 || 0) >= 0.8 &&
                      (evaluationResults.metrics.bertscore || 0) >= 0.85 && (
                        <div className="flex items-start space-x-3 p-3 bg-green-50 rounded-lg">
                          <span className="text-green-600">✅</span>
                          <div>
                            <div className="font-medium text-green-800">
                              Сильные стороны системы
                            </div>
                            <div className="text-sm text-green-700">
                              Хорошее извлечение информации и релевантность
                              ответов
                            </div>
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="metric-card text-center py-12">
                <div className="text-6xl mb-4">🔍</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {error ? "Ошибка при оценке" : "Запустите оценку системы"}
                </h3>
                <p className="text-gray-600">
                  {error
                    ? "Произошла ошибка при оценке системы. Проверьте настройки и попробуйте снова."
                    : "Нажмите кнопку 'Запустить оценку' для анализа качества работы системы на реальных данных"}
                </p>
                {error && (
                  <button
                    onClick={() => setError(null)}
                    className="mt-4 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-colors"
                  >
                    Попробовать снова
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Evaluation;
