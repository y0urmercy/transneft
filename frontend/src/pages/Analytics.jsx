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

      {/* Статистика бенчмарка */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="metric-card">
          <h3 className="text-sm font-medium text-gray-500">Всего QA пар</h3>
          <p className="text-2xl font-bold text-gray-900">
            {analyticsData?.benchmark_stats?.total_qa_pairs || 0}
          </p>
        </div>
        <div className="metric-card">
          <h3 className="text-sm font-medium text-gray-500">
            Уникальные секции
          </h3>
          <p className="text-2xl font-bold text-gray-900">
            {analyticsData?.system_metrics?.unique_sections || 0}
          </p>
        </div>
        <div className="metric-card">
          <h3 className="text-sm font-medium text-gray-500">Всего сообщений</h3>
          <p className="text-2xl font-bold text-gray-900">
            {analyticsData?.database_stats?.total_messages || 0}
          </p>
        </div>
      </div>

      {/* Дополнительная информация */}
      <div className="metric-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📈 Статистика системы
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-500">Активных сессий</div>
            <div className="text-lg font-semibold">
              {analyticsData?.database_stats?.total_sessions || 0}
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
            <div className="text-sm text-gray-500">Оцененных сообщений</div>
            <div className="text-lg font-semibold">
              {analyticsData?.database_stats?.rated_messages || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Время работы</div>
            <div className="text-lg font-semibold text-green-600">Активна</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
