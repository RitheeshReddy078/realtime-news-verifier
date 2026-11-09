import { BrowserRouter, Routes, Route } from "react-router-dom";

import Sidebar from "./components/layout/Sidebar";
import Topbar from "./components/layout/Topbar";

import Dashboard from "./pages/Dashboard";
import VerifyClaim from "./pages/VerifyClaim";
import History from "./pages/History";
import SystemStatus from "./pages/SystemStatus";
import SettingsPage from "./pages/Settings";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen overflow-x-hidden bg-[#080E1A] text-white">
        <Sidebar />

        {/* Main application content */}
        <div className="min-h-screen min-w-0 md:ml-64">
          <Topbar />

          <main className="min-w-0 p-4 sm:p-5 md:p-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/verify" element={<VerifyClaim />} />
              <Route path="/history" element={<History />} />
              <Route path="/status" element={<SystemStatus />} />
              <Route path="/settings" element={<SettingsPage />} />

              <Route
                path="*"
                element={
                  <div className="rounded-xl border border-slate-800 bg-[#111C2D] p-8 text-slate-300">
                    This page is coming soon.
                  </div>
                }
              />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
