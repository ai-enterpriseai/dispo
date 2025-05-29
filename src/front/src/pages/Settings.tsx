import React, { useState } from 'react';
import { useData } from '../context/DataContext';
import { Save, RefreshCcw } from 'lucide-react';

export const Settings: React.FC = () => {
  const { refreshData } = useData();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [settings, setSettings] = useState({
    refreshInterval: 5,
    maxTrucks: 50,
    maxOrders: 80,
    apiEndpoint: 'https://api.example.com/dispatch',
    apiKey: 'xxxx-xxxx-xxxx-xxxx'
  });

  const handleSettingChange = (key: string, value: any) => {
    setSettings({
      ...settings,
      [key]: value
    });
  };

  const handleRefreshData = async () => {
    setIsRefreshing(true);
    await refreshData();
    setTimeout(() => {
      setIsRefreshing(false);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Einstellungen</h1>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Systemkonfiguration</h2>
        </div>
        <div className="p-6">
          <div className="max-w-2xl space-y-6">
            <div>
              <h3 className="text-base font-medium text-gray-900 mb-4">Dateneinstellungen</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="refreshInterval" className="block text-sm font-medium text-gray-700">
                    Auto-Aktualisierungsintervall (Minuten)
                  </label>
                  <input
                    type="number"
                    id="refreshInterval"
                    value={settings.refreshInterval}
                    onChange={(e) => handleSettingChange('refreshInterval', parseInt(e.target.value))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    min="1"
                    max="60"
                  />
                </div>

                <div>
                  <label htmlFor="maxTrucks" className="block text-sm font-medium text-gray-700">
                    Maximale Anzahl anzuzeigender Fahrzeuge
                  </label>
                  <input
                    type="number"
                    id="maxTrucks"
                    value={settings.maxTrucks}
                    onChange={(e) => handleSettingChange('maxTrucks', parseInt(e.target.value))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    min="10"
                    max="200"
                  />
                </div>

                <div>
                  <label htmlFor="maxOrders" className="block text-sm font-medium text-gray-700">
                    Maximale Anzahl anzuzeigender Aufträge
                  </label>
                  <input
                    type="number"
                    id="maxOrders"
                    value={settings.maxOrders}
                    onChange={(e) => handleSettingChange('maxOrders', parseInt(e.target.value))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    min="10"
                    max="300"
                  />
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-6">
              <h3 className="text-base font-medium text-gray-900 mb-4">API-Konfiguration</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="apiEndpoint" className="block text-sm font-medium text-gray-700">
                    API-Endpunkt
                  </label>
                  <input
                    type="text"
                    id="apiEndpoint"
                    value={settings.apiEndpoint}
                    onChange={(e) => handleSettingChange('apiEndpoint', e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700">
                    API-Schlüssel
                  </label>
                  <input
                    type="password"
                    id="apiKey"
                    value={settings.apiKey}
                    onChange={(e) => handleSettingChange('apiKey', e.target.value)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>
              </div>
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="button"
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <Save className="h-4 w-4 mr-2" />
                Einstellungen speichern
              </button>
              <button
                type="button"
                onClick={handleRefreshData}
                disabled={isRefreshing}
                className={`inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${isRefreshing ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <RefreshCcw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                {isRefreshing ? 'Aktualisiere...' : 'Daten jetzt aktualisieren'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};