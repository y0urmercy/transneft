import axios from "axios";

// Для разработки - используем localhost
// Для продакшена нужно будет настроить переменные окружения в Vite
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api";

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
    return Promise.reject(error);
  }
);

export const chatAPI = {
  health: () => api.get("/health"),

  initialize: () => api.post("/initialize"),

  sendMessage: (data) => api.post("/chat", data),

  getChatHistory: (sessionId) => api.get(`/history/${sessionId}`),

  evaluateSystem: (sampleSize) =>
    api.post("/evaluate", { sample_size: sampleSize }),

  getAnalytics: () => api.get("/analytics"),

  getAdminStats: () => api.get("/admin/stats"),
};

export default api;
