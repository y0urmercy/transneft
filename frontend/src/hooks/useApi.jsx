import { useState, useEffect, useCallback } from "react";
import { chatAPI } from "../services/api";

export const useSystemHealth = () => {
  const [health, setHealth] = useState({
    status: "checking",
    system_ready: false,
  });
  const [loading, setLoading] = useState(true);

  const checkHealth = useCallback(async () => {
    try {
      const response = await chatAPI.health();
      setHealth(response.data);
    } catch (error) {
      setHealth({ status: "error", system_ready: false });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Проверка каждые 30 секунд
    return () => clearInterval(interval);
  }, [checkHealth]);

  return { health, loading, refresh: checkHealth };
};
