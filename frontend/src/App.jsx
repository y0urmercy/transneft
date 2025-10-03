import React, { useState, useEffect } from "react";
import { ChatProvider } from "./hooks/useChat";
import Layout from "./components/layout/Layout";
import Chat from "./pages/Chat";
import History from "./pages/History";
import Analytics from "./pages/Analytics";
import Evaluation from "./pages/Evaluation";
import Admin from "./pages/Admin";
import SystemStatus from "./components/common/SystemStatus";
import "./styles/globals.css";

function App() {
  const [currentPage, setCurrentPage] = useState("chat");

  // Обработка изменения страницы через хэш
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace("#", "");
      if (
        hash &&
        ["chat", "history", "analytics", "evaluation", "admin"].includes(hash)
      ) {
        setCurrentPage(hash);
      }
    };

    window.addEventListener("hashchange", handleHashChange);
    handleHashChange(); // Initial check

    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.location.hash = page;
  };

  const renderPage = () => {
    switch (currentPage) {
      case "chat":
        return <Chat />;
      case "history":
        return <History />;
      case "analytics":
        return <Analytics />;
      case "evaluation":
        return <Evaluation />;
      case "admin":
        return <Admin />;
      default:
        return <Chat />;
    }
  };

  return (
    <ChatProvider>
      <div className="min-h-screen bg-gray-50">
        <SystemStatus />
        <Layout currentPage={currentPage} onPageChange={handlePageChange}>
          {renderPage()}
        </Layout>
      </div>
    </ChatProvider>
  );
}

export default App;
