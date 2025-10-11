import React, { useState, useEffect } from "react";
import { chatAPI } from "../services/api";

const Analytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const response = await chatAPI.getAnalytics();
      setAnalyticsData(response.data);
    } catch (error) {
      console.error("Error loading analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center p-8">Загрузка аналитики...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">📊 Аналитика системы</h1>

      {/* Основная статистика */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="metric-card">
          <h3 className="text-sm font-medium text-gray-500">Всего вопросов</h3>
          <p className="text-2xl font-bold text-gray-900">
            {analyticsData?.total_questions || 0}
          </p>
        </div>
        <div className="metric-card">
          <h3 className="text-sm font-medium text-gray-500">Активных сессий</h3>
          <p className="text-2xl font-bold text-gray-900">
            {analyticsData?.active_sessions || 0}
          </p>
        </div>
      </div>

      {/* Статистика базы данных */}
      <div className="metric-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📈 Статистика базы данных
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-500">Всего сообщений</div>
            <div className="text-lg font-semibold">
              {analyticsData?.database_stats?.total_messages || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Оцененных сообщений</div>
            <div className="text-lg font-semibold">
              {analyticsData?.database_stats?.rated_messages || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Средняя оценка</div>
            <div className="text-lg font-semibold">
              {analyticsData?.database_stats?.avg_rating > 0
                ? `${analyticsData.database_stats.avg_rating.toFixed(1)}⭐`
                : "Нет оценок"}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Среднее время ответа</div>
            <div className="text-lg font-semibold">
              {analyticsData?.database_stats?.avg_response_time?.toFixed(2) ||
                "0.00"}
              с
            </div>
          </div>
        </div>
      </div>

      {/* Статистика бенчмарка */}
      {analyticsData?.benchmark_stats && (
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            🎯 Статистика бенчмарка
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-500">Точность</div>
              <div className="text-lg font-semibold text-green-600">
                {((analyticsData.benchmark_stats.accuracy || 0) * 100).toFixed(
                  1
                )}
                %
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Время ответа</div>
              <div className="text-lg font-semibold">
                {analyticsData.benchmark_stats.response_time?.toFixed(2) ||
                  "0.00"}
                с
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Всего чанков</div>
              <div className="text-lg font-semibold">
                {analyticsData.benchmark_stats.total_chunks || 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Информация о системе */}
      <div className="metric-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          ℹ️ Информация о системе
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-500">Время работы:</span>
            <span>{analyticsData?.system_uptime || "Неизвестно"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Статус:</span>
            <span className="text-green-600 font-medium">Активна</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
