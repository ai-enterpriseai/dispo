import React, { useState } from 'react';
import { useData } from '../../context/DataContext';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

export const OptimizationResults: React.FC = () => {
  const { 
    trucks, 
    orders, 
    assignments, 
    fleetUtilization, 
    totalDistance, 
    unassignedOrders, 
    lastOptimized 
  } = useData();
  
  const [chartType, setChartType] = useState<'utilization' | 'distance'>('utilization');

  // For demonstration purposes, we'll create some fake historical data
  // In a real app, this would come from an API
  const previousMetrics = {
    fleetUtilization: fleetUtilization * 0.8,
    totalDistance: totalDistance * 1.2,
    unassignedOrders: unassignedOrders * 1.5
  };

  const utilizationData = [
    {
      name: 'Vorher',
      value: previousMetrics.fleetUtilization
    },
    {
      name: 'Nachher',
      value: fleetUtilization
    }
  ];

  const distanceData = [
    {
      name: 'Vorher',
      value: previousMetrics.totalDistance
    },
    {
      name: 'Nachher',
      value: totalDistance
    }
  ];

  const unassignedData = [
    {
      name: 'Vorher',
      value: previousMetrics.unassignedOrders
    },
    {
      name: 'Nachher',
      value: unassignedOrders
    }
  ];

  // Pie chart data for truck status distribution
  const truckStatusData = () => {
    const statusCounts: Record<string, number> = {};
    
    trucks.forEach(truck => {
      const statusKey = getTruckStatusText(truck.status);
      statusCounts[statusKey] = (statusCounts[statusKey] || 0) + 1;
    });
    
    return Object.entries(statusCounts).map(([status, count]) => ({
      name: status,
      value: count
    }));
  };

  // Pie chart data for order priority distribution
  const orderPriorityData = () => {
    const priorityCounts: Record<string, number> = {};
    
    orders.forEach(order => {
      const priorityKey = `Priorität ${order.priority}`;
      priorityCounts[priorityKey] = (priorityCounts[priorityKey] || 0) + 1;
    });
    
    return Object.entries(priorityCounts).map(([priority, count]) => ({
      name: priority,
      value: count
    }));
  };

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

  const getTruckStatusText = (status: string) => {
    switch (status) {
      case 'idle': return 'Inaktiv';
      case 'loading': return 'Beladen';
      case 'en-route': return 'Unterwegs';
      case 'delivering': return 'Liefernd';
      case 'maintenance': return 'Wartung';
      default: return status;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">Optimierungsergebnisse</h2>
        {lastOptimized ? (
          <p className="text-sm text-gray-500">
            Letzte Optimierung: {lastOptimized.toLocaleString('de-DE')}
          </p>
        ) : (
          <p className="text-sm text-gray-500">Noch keine Optimierung durchgeführt</p>
        )}
      </div>
      
      <div className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Flottenauslastung</h3>
            <div className="flex items-baseline">
              <p className="text-2xl font-semibold text-gray-900">{fleetUtilization.toFixed(1)}%</p>
              {fleetUtilization > previousMetrics.fleetUtilization ? (
                <p className="ml-2 text-sm text-green-600">
                  +{(fleetUtilization - previousMetrics.fleetUtilization).toFixed(1)}%
                </p>
              ) : (
                <p className="ml-2 text-sm text-red-600">
                  {(fleetUtilization - previousMetrics.fleetUtilization).toFixed(1)}%
                </p>
              )}
            </div>
            <div className="mt-1 text-xs text-gray-500">
              Vorher: {previousMetrics.fleetUtilization.toFixed(1)}%
            </div>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Gesamtstrecke</h3>
            <div className="flex items-baseline">
              <p className="text-2xl font-semibold text-gray-900">{totalDistance.toLocaleString()} km</p>
              {totalDistance < previousMetrics.totalDistance ? (
                <p className="ml-2 text-sm text-green-600">
                  -{(previousMetrics.totalDistance - totalDistance).toLocaleString()}
                </p>
              ) : (
                <p className="ml-2 text-sm text-red-600">
                  +{(totalDistance - previousMetrics.totalDistance).toLocaleString()}
                </p>
              )}
            </div>
            <div className="mt-1 text-xs text-gray-500">
              Vorher: {previousMetrics.totalDistance.toLocaleString()} km
            </div>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Nicht zugewiesene Aufträge</h3>
            <div className="flex items-baseline">
              <p className="text-2xl font-semibold text-gray-900">{unassignedOrders}</p>
              {unassignedOrders < previousMetrics.unassignedOrders ? (
                <p className="ml-2 text-sm text-green-600">
                  -{(previousMetrics.unassignedOrders - unassignedOrders)}
                </p>
              ) : (
                <p className="ml-2 text-sm text-red-600">
                  +{(unassignedOrders - previousMetrics.unassignedOrders)}
                </p>
              )}
            </div>
            <div className="mt-1 text-xs text-gray-500">
              Vorher: {previousMetrics.unassignedOrders}
            </div>
          </div>
        </div>
        
        <div className="space-y-6">
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Vorher/Nachher Vergleich</h3>
              <div className="flex space-x-2">
                <button
                  onClick={() => setChartType('utilization')}
                  className={`px-3 py-1 text-sm rounded ${
                    chartType === 'utilization' 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Auslastung
                </button>
                <button
                  onClick={() => setChartType('distance')}
                  className={`px-3 py-1 text-sm rounded ${
                    chartType === 'distance' 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Entfernung
                </button>
              </div>
            </div>
            
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartType === 'utilization' ? utilizationData : distanceData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value) => [
                      chartType === 'utilization' 
                        ? `${value.toFixed(1)}%` 
                        : `${value.toLocaleString()} km`, 
                      chartType === 'utilization' ? 'Auslastung' : 'Entfernung'
                    ]}
                  />
                  <Legend />
                  <Bar 
                    dataKey="value" 
                    fill={chartType === 'utilization' ? '#3B82F6' : '#10B981'}
                    animationDuration={1500}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-4">Fahrzeugstatus-Verteilung</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={truckStatusData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {truckStatusData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [`${value} Fahrzeuge`, '']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-4">Auftrags-Prioritätsverteilung</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={orderPriorityData()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {orderPriorityData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [`${value} Aufträge`, '']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};