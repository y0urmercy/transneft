// src/components/layout/Layout.jsx
import React, { useState } from "react";
import Header from "./Header";
import Sidebar from "./Sidebar";
import Avatar from "../common/Avatar";

const Layout = ({ children, currentPage, onPageChange }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [avatarState, setAvatarState] = useState("idle");

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        currentPage={currentPage}
        onPageChange={onPageChange}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header
          onMenuClick={() => setSidebarOpen(true)}
          currentPage={currentPage}
        />

        <main className="flex-1 overflow-hidden flex">
          {/* Avatar Section */}
          <div className="w-80 border-r border-gray-200 bg-white hidden lg:flex flex-col items-center p-6">
            <Avatar state={avatarState} onStateChange={setAvatarState} />
            <div className="mt-4 text-center">
              <h3 className="text-lg font-semibold text-gray-800">-</h3>
              <p className="text-sm text-gray-600">
                Эксперт по ПАО "Транснефть"
              </p>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-auto">{children}</div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
