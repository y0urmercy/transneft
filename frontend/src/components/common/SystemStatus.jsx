import React from "react";
import { useSystemHealth } from "../../hooks/useApi";

const SystemStatus = () => {
  const { health, loading } = useSystemHealth();

  if (loading) {
    return (
      <div className="bg-blue-50 border-b border-blue-200 px-4 py-2">
        <div className="flex items-center justify-center text-sm text-blue-700">
          <div className="w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2"></div>
          Проверка статуса системы...
        </div>
      </div>
    );
  }

  if (health.status === "healthy" && health.system_ready) {
    return (
      <div className="bg-green-50 border-b border-green-200 px-4 py-2">
        <div className="flex items-center justify-center text-sm text-green-700">
          <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
          Система готова к работе
        </div>
      </div>
    );
  }

  return (
    <div className="bg-yellow-50 border-b border-yellow-200 px-4 py-2">
      <div className="flex items-center justify-center text-sm text-yellow-700">
        <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
        Система инициализируется... Некоторые функции могут быть недоступны
      </div>
    </div>
  );
};

export default SystemStatus;
