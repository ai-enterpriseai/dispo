import React from 'react';
import { useData } from '../../context/DataContext';
import { Sliders, PlayCircle } from 'lucide-react';

export const OptimizationPanel: React.FC = () => {
  const { 
    runOptimization, 
    isOptimizing 
  } = useData();

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-lg font-medium text-gray-900 flex items-center">
          <Sliders className="h-5 w-5 mr-2 text-blue-600" />
          Optimierungssteuerung
        </h2>
      </div>
      <div className="p-6">
        <button
          onClick={runOptimization}
          disabled={isOptimizing}
          className={`w-full flex items-center justify-center px-4 py-3 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
            isOptimizing ? 'opacity-70 cursor-not-allowed' : ''
          }`}
        >
          <PlayCircle className="h-5 w-5 mr-2" />
          {isOptimizing ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Optimierung läuft...
            </span>
          ) : (
            'Optimierung starten'
          )}
        </button>
      </div>
    </div>
  );
};