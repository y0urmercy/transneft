import axios from "axios";

const API_BASE_URL = "http://localhost:8001/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error);

    // Детальная информация об ошибке
    if (error.response) {
      console.error("Error details:", {
        status: error.response.status,
        message: error.response.data?.detail || error.message,
        url: error.config?.url,
      });
    } else if (error.request) {
      console.error("No response received:", error.request);
    } else {
      console.error("Request setup error:", error.message);
    }

    return Promise.reject(error);
  }
);

export const chatAPI = {
  // Health & System
  health: () => api.get("/health"),
  initialize: () => api.post("/initialize"),
  getSystemStatus: () => api.get("/system/status"),
  reloadSystem: () => api.post("/system/reload"),

  // Chat
  sendMessage: (data) => api.post("/chat", data),
  getChatHistory: (sessionId) => api.get(`/history/${sessionId}`),

  // Evaluation & Analytics
  evaluateSystem: (sampleSize) =>
    api.post("/evaluate", { sample_size: sampleSize }),
  getAnalytics: () => api.get("/analytics"),
  getBenchmarkStats: () => api.get("/benchmark/stats"),

  // Feedback
  submitFeedback: (data) => api.post("/feedback", data),
};

// Вспомогательные функции
export const apiUtils = {
  // Проверка доступности API
  checkAPIHealth: async () => {
    try {
      await chatAPI.health();
      return true;
    } catch {
      return false;
    }
  },

  // Создание сессии
  generateSessionId: () => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  },

  // Обработка ошибок с повторными попытками
  retryRequest: async (request, retries = 3, delay = 1000) => {
    try {
      return await request();
    } catch (error) {
      if (retries > 0) {
        await new Promise((resolve) => setTimeout(resolve, delay));
        return apiUtils.retryRequest(request, retries - 1, delay * 2);
      }
      throw error;
    }
  },
};

export default api;
