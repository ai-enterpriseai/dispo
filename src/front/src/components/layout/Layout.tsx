import React, { ReactNode, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Truck, 
  Map, 
  BarChart3, 
  Settings as SettingsIcon,
  Menu,
  X,
  RefreshCcw,
  Download,
  Clock
} from 'lucide-react';
import { useData } from '../../context/DataContext';
import { format } from 'date-fns';

interface LayoutProps {
  children: ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { lastUpdated, lastOptimized, refreshData, exportData } = useData();
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/', icon: <Truck size={20} />, label: 'Dashboard' },
    { path: '/map', icon: <Map size={20} />, label: 'Kartenansicht' },
    { path: '/analysis', icon: <BarChart3 size={20} />, label: 'Analyse' },
    { path: '/settings', icon: <SettingsIcon size={20} />, label: 'Einstellungen' }
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Mobile sidebar toggle */}
      <button
        className="md:hidden fixed z-50 bottom-4 right-4 p-2 rounded-full bg-blue-600 text-white shadow-lg"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Sidebar */}
      <div 
        className={`fixed md:static inset-y-0 left-0 z-40 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0`}
      >
        <div className="flex flex-col h-full">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center space-x-2">
              <Truck className="h-6 w-6 text-blue-600" />
              <span className="font-bold text-xl">TruckMatch</span>
            </div>
            <p className="text-sm text-gray-500">Flottenmanagementsystem</p>
          </div>

          <nav className="flex-1 px-4 py-4">
            <ul className="space-y-2">
              {navItems.map((item) => (
                <li key={item.path}>
                  <button
                    onClick={() => {
                      navigate(item.path);
                      if (window.innerWidth < 768) {
                        setSidebarOpen(false);
                      }
                    }}
                    className={`flex items-center w-full px-4 py-2 rounded-lg transition-colors ${
                      location.pathname === item.path
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {item.icon}
                    <span className="ml-3">{item.label}</span>
                  </button>
                </li>
              ))}
            </ul>
          </nav>

          <div className="px-6 py-4 border-t border-gray-200">
            <div className="flex flex-col space-y-2">
              <div className="flex items-center text-sm text-gray-500">
                <Clock size={14} className="mr-1" />
                <span>Letztes Update: {format(lastUpdated, 'HH:mm')}</span>
              </div>
              {lastOptimized && (
                <div className="flex items-center text-sm text-gray-500">
                  <Clock size={14} className="mr-1" />
                  <span>Letzte Optimierung: {format(lastOptimized, 'HH:mm')}</span>
                </div>
              )}
              <div className="flex space-x-2 mt-2">
                <button
                  onClick={refreshData}
                  className="flex items-center justify-center px-3 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded transition-colors"
                >
                  <RefreshCcw size={14} className="mr-1" />
                  Aktualisieren
                </button>
                <button
                  onClick={exportData}
                  className="flex items-center justify-center px-3 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded transition-colors"
                >
                  <Download size={14} className="mr-1" />
                  Exportieren
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
};