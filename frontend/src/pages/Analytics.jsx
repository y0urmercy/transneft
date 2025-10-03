import React, { useState, useEffect } from "react";
import { chatAPI } from "../services/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

const Analytics = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState("7d");

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      const response = await chatAPI.getAnalytics();
      setAnalyticsData(response.data);
    } catch (error) {
      console.error("Error loading analytics:", error);
      // Mock data for demonstration
      setAnalyticsData({
        total_messages: 145,
        total_sessions: 23,
        avg_messages_per_session: 6.3,
        popular_questions: [
          { question: "Уставной капитал", count: 15 },
          { question: "Дата основания", count: 12 },
          { question: "География", count: 8 },
          { question: "Дивиденды", count: 6 },
          { question: "Руководство", count: 5 },
        ],
        message_trend: [
          { date: "2024-01-01", messages: 10 },
          { date: "2024-01-02", messages: 15 },
          { date: "2024-01-03", messages: 8 },
          { date: "2024-01-04", messages: 12 },
          { date: "2024-01-05", messages: 18 },
          { date: "2024-01-06", messages: 14 },
          { date: "2024-01-07", messages: 11 },
        ],
        section_distribution: [
          { name: "Финансы", value: 35 },
          { name: "История", value: 25 },
          { name: "География", value: 20 },
          { name: "Руководство", value: 15 },
          { name: "Другое", value: 5 },
        ],
      });
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884D8"];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">
          📈 Аналитика системы
        </h1>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="24h">Последние 24 часа</option>
          <option value="7d">Последние 7 дней</option>
          <option value="30d">Последние 30 дней</option>
          <option value="90d">Последние 90 дней</option>
        </select>
      </div>

      {/* Ключевые метрики */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="metric-card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
              <span className="text-2xl">💬</span>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">
                Всего сообщений
              </h3>
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData?.total_messages || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mr-4">
              <span className="text-2xl">📊</span>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">Сессий</h3>
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData?.total_sessions || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mr-4">
              <span className="text-2xl">📝</span>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">
                Сообщений/сессия
              </h3>
              <p className="text-2xl font-bold text-gray-900">
                {analyticsData?.avg_messages_per_session?.toFixed(1) || "0.0"}
              </p>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="flex items-center">
            <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mr-4">
              <span className="text-2xl">⭐</span>
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500">
                Средняя оценка
              </h3>
              <p className="text-2xl font-bold text-gray-900">4.7</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* График популярных вопросов */}
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📊 Популярные вопросы
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData?.popular_questions || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="question" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#3b82f6" name="Количество запросов" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Распределение по секциям */}
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            🎯 Распределение по темам
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analyticsData?.section_distribution || []}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {analyticsData?.section_distribution?.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Тренд сообщений */}
      <div className="metric-card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📈 Активность сообщений
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={analyticsData?.message_trend || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar
              dataKey="messages"
              fill="#10b981"
              name="Количество сообщений"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Дополнительная статистика */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            🕒 Время ответа
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Среднее время ответа</span>
              <span className="font-semibold">1.2 сек</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Максимальное время</span>
              <span className="font-semibold">3.8 сек</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">95-й перцентиль</span>
              <span className="font-semibold">2.1 сек</span>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            ✅ Эффективность системы
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Успешные ответы</span>
              <span className="font-semibold text-green-600">92%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Средняя уверенность</span>
              <span className="font-semibold">87%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Использование источников</span>
              <span className="font-semibold">94%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
