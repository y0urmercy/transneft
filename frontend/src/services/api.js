// src/services/api.js
const API_BASE_URL =
  process.env.REACT_APP_API_URL || "http://localhost:8000/api";

export const chatAPI = {
  initialize: async () => {
    const response = await fetch(`${API_BASE_URL}/initialize`, {
      method: "POST",
    });
    return response.json();
  },

  sendMessage: async (data) => {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  getChatHistory: async (sessionId) => {
    const response = await fetch(`${API_BASE_URL}/history/${sessionId}`);
    return response.json();
  },

  evaluateSystem: async (sampleSize) => {
    const response = await fetch(`${API_BASE_URL}/evaluate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ sample_size: sampleSize }),
    });
    return response.json();
  },

  getAnalytics: async () => {
    const response = await fetch(`${API_BASE_URL}/analytics`);
    return response.json();
  },
};
