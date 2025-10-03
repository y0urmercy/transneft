export const formatDate = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const formatTime = (dateString) => {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const generateSessionId = () => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export const exportToJson = (data, filename) => {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename}_${new Date().toISOString().split("T")[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

export const calculateQualityLevel = (score) => {
  if (score >= 0.9)
    return {
      level: "Отличное",
      color: "text-green-600",
      bgColor: "bg-green-100",
    };
  if (score >= 0.8)
    return { level: "Хорошее", color: "text-blue-600", bgColor: "bg-blue-100" };
  if (score >= 0.7)
    return {
      level: "Удовлетворительное",
      color: "text-yellow-600",
      bgColor: "bg-yellow-100",
    };
  return {
    level: "Требует улучшения",
    color: "text-red-600",
    bgColor: "bg-red-100",
  };
};
