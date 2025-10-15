import React, { useState, useEffect } from "react";
import { ChatProvider } from "./hooks/useChat";
import Layout from "./components/layout/Layout";
import Chat from "./pages/Chat";
import History from "./pages/History";
import Evaluation from "./pages/Evaluation";
import SystemStatus from "./components/common/SystemStatus";
import "./styles/globals.css";

function App() {
  const [currentPage, setCurrentPage] = useState("chat");

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace("#", "");
      if (hash && ["chat", "history", "evaluation"].includes(hash)) {
        setCurrentPage(hash);
      }
    };

    window.addEventListener("hashchange", handleHashChange);
    handleHashChange();

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
