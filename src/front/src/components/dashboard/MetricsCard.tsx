import React from 'react';
import { useData } from '../../context/DataContext';
import { Truck, Package, Loader as Road } from 'lucide-react';

export const MetricsCard: React.FC = () => {
  const { 
    trucks, 
    orders, 
    fleetUtilization, 
    totalDistance, 
    unassignedOrders 
  } = useData();

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="bg-white rounded-lg shadow p-6 flex items-start space-x-4">
        <div className="rounded-full bg-blue-100 p-3">
          <Truck className="h-6 w-6 text-blue-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500">Flottenauslastung</p>
          <div className="mt-1 flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900">{fleetUtilization.toFixed(1)}%</p>
            <p className="ml-2 text-sm text-gray-500">
              ({trucks.length} Fahrzeuge)
            </p>
          </div>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full" 
              style={{ width: `${fleetUtilization}%` }} 
            />
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 flex items-start space-x-4">
        <div className="rounded-full bg-green-100 p-3">
          <Road className="h-6 w-6 text-green-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500">Gesamtstrecke</p>
          <div className="mt-1 flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900">{totalDistance.toLocaleString()}</p>
            <p className="ml-2 text-sm text-gray-500">km</p>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Durchschnitt: {trucks.length > 0 ? (totalDistance / trucks.length).toFixed(1) : 0} pro Fahrzeug
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6 flex items-start space-x-4">
        <div className="rounded-full bg-amber-100 p-3">
          <Package className="h-6 w-6 text-amber-600" />
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500">Auftragsstatus</p>
          <div className="mt-1 flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900">{unassignedOrders}</p>
            <p className="ml-2 text-sm text-gray-500">nicht zugewiesen</p>
          </div>
          <p className="mt-1 text-sm text-gray-500">
            {orders.length} Aufträge insgesamt ({((orders.length - unassignedOrders) / orders.length * 100).toFixed(1)}% zugewiesen)
          </p>
        </div>
      </div>
    </div>
  );
};