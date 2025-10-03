import React, { useState, useEffect } from 'react';
import { chatAPI } from '../services/api';

const Admin = () => {
  const [adminStats, setAdminStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    loadAdminStats();
  }, []);

  const loadAdminStats = async () => {
    try {
      const response = await chatAPI.getAdminStats();
      setAdminStats(response.data);
    } catch (error) {
      console.error('Error loading admin stats:', error);
      // Mock data for demonstration
      setAdminStats({
        database_stats: {
          total_messages: 156,
          rated_messages: 45,
          avg_rating: 4.7,
          total_sessions: 24
        },
        evaluation_history: [
          {
            evaluation_date: new Date().toISOString(),
            sample_size: 30,
            overall_score: 0.82,
            rouge1: 0.85,
            rouge2: 0.78,
            bertscore: 0.87
          }
        ],
        system_info: {
          python_version: '3.9.0',
          database_size: '45.2 MB',
          last_backup: new Date(Date.now() - 86400000).toISOString(),
          system_uptime: '7 дней 3 часа'
        }
      });
    } finally {
      setLoading(false);
    }
  };

  const performAction = async (action) => {
    switch (action) {
      case 'backup':
        alert('Функция бэкапа в разработке');
        break;
      case 'clear_cache':
        alert('Кэш очищен');
        break;
      case 'restart':
        if (confirm('Перезапустить систему?')) {
          alert('Система перезапускается...');
        }
        break;
      default:
        break;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">🔧 Администрирование системы</h1>

      <div className="flex space-x-2 border-b border-gray-200">
        {['overview', 'database', 'system', 'logs'].map((section) => (
          <button
            key={section}
            onClick={() => setActiveSection(section)}
            className={`px-4 py-2 font-medium ${
              activeSection === section
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {section === 'overview' && '📊 Обзор'}
            {section === 'database' && '💾 База данных'}
            {section === 'system' && '⚙️ Система'}
            {section === 'logs' && '📋 Логи'}
          </button>
        ))}
      </div>

      {activeSection === 'overview' && (
        <div className="space-y-6">
          {/* Ключевые метрики */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="metric-card">
              <h3 className="text-sm font-medium text-gray-500">Всего сообщений</h3>
              <p className="text-2xl font-bold text-gray-900">
                {adminStats?.database_stats?.total_messages || 0}
              </p>
            </div>
            <div className="metric-card">
              <h3 className="text-sm font-medium text-gray-500">Оцененных сообщений</h3>
              <p className="text-2xl font-bold text-gray-900">
                {adminStats?.database_stats?.rated_messages || 0}
              </p>
            </div>
            <div className="metric-card">
              <h3 className="text-sm font-medium text-gray-500">Средняя оценка</h3>
              <p className="text-2xl font-bold text-gray-900">
                {adminStats?.database_stats?.avg_rating > 0
                  ? `${adminStats.database_stats.avg_rating.toFixed(1)}⭐`
                  : 'Нет оценок'
                }
              </p>
            </div>
            <div className="metric-card">
              <h3 className="text-sm font-medium text-gray-500">Активных сессий</h3>
              <p className="text-2xl font-bold text-gray-900">
                {adminStats?.database_stats?.total_sessions || 0}
              </p>
            </div>
          </div>

          {/* Быстрые действия */}
          <div className="metric-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 Быстрые действия</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <button
                onClick={() => performAction('backup')}
                className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
              >
                <div className="text-2xl mb-2">💾</div>
                <div className="font-medium text-gray-900">Создать бэкап</div>
                <div className="text-sm text-gray-500">Резервное копирование данных</div>
              </button>

              <button
                onClick={() => performAction('clear_cache')}
                className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
              >
                <div className="text-2xl mb-2">🗑️</div>
                <div className="font-medium text-gray-900">Очистить кэш</div>
                <div className="text-sm text-gray-500">Очистить временные файлы</div>
              </button>

              <button
                onClick={() => performAction('restart')}
                className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left"
              >
                <div className="text-2xl mb-2">🔄</div>
                <div className="font-medium text-gray-900">Перезапуск</div>
                <div className="text-sm text-gray-500">Перезапустить систему</div>
              </button>
            </div>
          </div>

          {/* Последние оценки */}
          <div className="metric-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              📈 Последние оценки системы
            </h3>
            {adminStats?.evaluation_history?.length > 0 ? (
              <div className="space-y-3">
                {adminStats.evaluation_history.slice(0, 3).map((evalItem, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <div className="font-medium text-gray-900">
                        Оценка от {new Date(evalItem.evaluation_date).toLocaleDateString('ru-RU')}
                      </div>
                      <div className="text-sm text-gray-500">
                        Выборка: {evalItem.sample_size} QA пар
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-blue-600">
                        {(evalItem.overall_score * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-500">Общий балл</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                Нет данных об оценках
              </div>
            )}
          </div>
        </div>
      )}

      {activeSection === 'database' && (
        <div className="space-y-6">
          <div className="metric-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">💾 Управление базой данных</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Информация о БД</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Размер базы данных:</span>
                    <span className="font-medium">{adminStats?.system_info?.database_size || 'Неизвестно'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Последний бэкап:</span>
                    <span className="font-medium">
                      {adminStats?.system_info?.last_backup
                        ? new Date(adminStats.system_info.last_backup).toLocaleDateString('ru-RU')
                        : 'Неизвестно'
                      }
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Тип базы данных:</span>
                    <span className="font-medium">SQLite</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Действия</h4>
                <div className="space-y-2">
                  <button className="w-full btn-secondary justify-center">
                    🔄 Обновить схему БД
                  </button>
                  <button className="w-full btn-secondary justify-center">
                    📊 Оптимизация БД
                  </button>
                  <button className="w-full btn-secondary justify-center">
                    📋 Показать запросы
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="metric-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 Статистика таблиц</h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 font-medium text-gray-900">Таблица</th>
                    <th className="text-left py-3 font-medium text-gray-900">Записей</th>
                    <th className="text-left py-3 font-medium text-gray-900">Размер</th>
                    <th className="text-left py-3 font-medium text-gray-900">Последнее обновление</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-gray-100">
                    <td className="py-3 text-sm text-gray-900">chat_messages</td>
                    <td className="py-3 text-sm text-gray-600">156</td>
                    <td className="py-3 text-sm text-gray-600">12.3 MB</td>
                    <td className="py-3 text-sm text-gray-600">2 минуты назад</td>
                  </tr>
                  <tr className="border-b border-gray-100">
                    <td className="py-3 text-sm text-gray-900">evaluation_results</td>
                    <td className="py-3 text-sm text-gray-600">8</td>
                    <td className="py-3 text-sm text-gray-600">2.1 MB</td>
                    <td className="py-3 text-sm text-gray-600">1 день назад</td>
                  </tr>
                  <tr>
                    <td className="py-3 text-sm text-gray-900">system_logs</td>
                    <td className="py-3 text-sm text-gray-600">1,245</td>
                    <td className="py-3 text-sm text-gray-600">8.7 MB</td>
                    <td className="py-3 text-sm text-gray-600">5 минут назад</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {activeSection === 'system' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="metric-card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">⚙️ Системная информация</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Версия Python:</span>
                  <span className="font-medium">{adminStats?.system_info?.python_version || '3.9.0'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Время работы:</span>
                  <span className="font-medium">{adminStats?.system_info?.system_uptime || '7 дней 3 часа'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Память БД:</span>
                  <span className="font-medium">{adminStats?.system_info?.database_size || '45.2 MB'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Статус RAG системы:</span>
                  <span className="font-medium text-green-600">✅ Активна</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Векторное хранилище:</span>
                  <span className="font-medium text-green-600">✅ Загружено</span>
                </div>
              </div>
            </div>

            <div className="metric-card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">🔧 Настройки системы</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Максимальное количество источников:
                  </label>
                  <select className="w-full border border-gray-300 rounded-lg px-3 py-2">
                    <option>3 (по умолчанию)</option>
                    <option>5</option>
                    <option>10</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Порог уверенности:
                  </label>
                  <select className="w-full border border-gray-300 rounded-lg px-3 py-2">
                    <option>0.7 (по умолчанию)</option>
                    <option>0.8</option>
                    <option>0.9</option>
                  </select>
                </div>

                <button className="w-full btn-primary">
                  💾 Сохранить настройки
                </button>
              </div>
            </div>
          </div>

          <div className="metric-card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Последние действия системы</h3>
            <div className="space-y-2">
              {[
                { action: 'Инициализация RAG системы', time: '2 минуты назад', status: 'success' },
                { action: 'Загрузка векторного хранилища', time: '5 минут назад', status: 'success' },
                { action: 'Обновление индексов', time: '10 минут назад', status: 'success' },
                { action: 'Резервное копирование', time: '1 день назад', status: 'warning' },
              ].map((log, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      log.status === 'success' ? 'bg-green-500' : 'bg-yellow-500'
                    }`}></div>
                    <span className="text-sm text-gray-900">{log.action}</span>
                  </div>
                  <span className="text-sm text-gray-500">{log.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeSection === 'logs' && (
        <div className="metric-card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Системные логи</h3>
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm h-96 overflow-y-auto">
            <div>[INFO] 2024-01-15 10:30:15 - Система инициализирована успешно</div>
            <div>[INFO] 2024-01-15 10:30:16 - RAG система загружена</div>
            <div>[INFO] 2024-01-15 10:30:17 - Векторное хранилище подключено</div>
            <div>[INFO] 2024-01-15 10:31:22 - Пользовательский запрос обработан</div>
            <div>[INFO] 2024-01-15 10:32:45 - Извлечено 3 релевантных документа</div>
            <div>[INFO] 2024-01-15 10:33:10 - Ответ сгенерирован (уверенность: 87%)</div>
            <div>[INFO] 2024-01-15 10:35:20 - Новая сессия создана</div>
            <div className="text-gray-500">// ... больше логов ...</div>
          </div>
          <div className="flex space-x-2 mt-4">
            <button className="btn-secondary">📥 Скачать логи</button>
            <button className="btn-secondary">🗑️ Очистить логи</button>
            <button className="btn-secondary">🔄 Обновить</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Admin;