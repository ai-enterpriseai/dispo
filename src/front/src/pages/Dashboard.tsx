import React from 'react';
import { MetricsCard } from '../components/dashboard/MetricsCard';
import { AssignmentsTable } from '../components/dashboard/AssignmentsTable';
import { OptimizationPanel } from '../components/dashboard/OptimizationPanel';
import { useData } from '../context/DataContext';
import { Truck, Package, Clock, MapPin } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { trucks, orders, assignments } = useData();

  // Get unassigned trucks and orders
  const assignedTruckIds = new Set(assignments.map(a => a.truckId));
  const assignedOrderIds = new Set(assignments.map(a => a.orderId));
  
  const unassignedTrucks = trucks.filter(truck => !assignedTruckIds.has(truck.id));
  const unassignedOrders = orders.filter(order => !assignedOrderIds.has(order.id));

  const getTruckStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return 'bg-gray-100 text-gray-800';
      case 'loading': return 'bg-blue-100 text-blue-800';
      case 'en-route': return 'bg-green-100 text-green-800';
      case 'delivering': return 'bg-purple-100 text-purple-800';
      case 'maintenance': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTruckStatusText = (status: string) => {
    switch (status) {
      case 'idle': return 'Verfügbar';
      case 'loading': return 'Beladen';
      case 'en-route': return 'Unterwegs';
      case 'delivering': return 'Liefernd';
      case 'maintenance': return 'Wartung';
      default: return status;
    }
  };

  const getOrderPriorityColor = (priority: number) => {
    switch (priority) {
      case 1: return 'bg-red-100 text-red-800';
      case 2: return 'bg-amber-100 text-amber-800';
      case 3: return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      </div>

      <MetricsCard />

      {/* Show unassigned trucks and orders when there are no assignments */}
      {assignments.length === 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Unassigned Trucks */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900 flex items-center">
                <Truck className="h-5 w-5 mr-2 text-blue-600" />
                Verfügbare Fahrzeuge ({unassignedTrucks.length})
              </h2>
            </div>
            <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
              {unassignedTrucks.map((truck) => (
                <div key={truck.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center rounded-full bg-blue-100 text-blue-700">
                        <Truck className="h-5 w-5" />
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{truck.name}</div>
                        <div className="text-sm text-gray-500">{truck.driver}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getTruckStatusColor(truck.status)}`}>
                        {getTruckStatusText(truck.status)}
                      </span>
                      <div className="text-xs text-gray-500 mt-1">
                        {truck.capacity.toLocaleString()} kg
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center text-xs text-gray-500">
                    <Clock className="h-3 w-3 mr-1" />
                    Verfügbar: {truck.availableFrom.toFixed(1)} - {truck.availableTo.toFixed(1)} Uhr
                  </div>
                </div>
              ))}
              {unassignedTrucks.length === 0 && (
                <div className="px-6 py-4 text-center text-sm text-gray-500">
                  Alle Fahrzeuge sind zugewiesen
                </div>
              )}
            </div>
          </div>

          {/* Unassigned Orders */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900 flex items-center">
                <Package className="h-5 w-5 mr-2 text-amber-600" />
                Offene Aufträge ({unassignedOrders.length})
              </h2>
            </div>
            <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
              {unassignedOrders.map((order) => (
                <div key={order.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center rounded-full bg-amber-100 text-amber-700">
                        <Package className="h-5 w-5" />
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{order.customer}</div>
                        <div className="text-sm text-gray-500 flex items-center">
                          <MapPin className="h-3 w-3 mr-1" />
                          {order.pickupLocation.address.substring(0, 25)}...
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getOrderPriorityColor(order.priority)}`}>
                        Priorität {order.priority}
                      </span>
                      <div className="text-xs text-gray-500 mt-1">
                        {order.weight.toLocaleString()} kg
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 flex items-center text-xs text-gray-500">
                    <Clock className="h-3 w-3 mr-1" />
                    Ladezeit: {order.loadingDuration.toFixed(1)}h | Entladezeit: {order.unloadingDuration.toFixed(1)}h
                  </div>
                </div>
              ))}
              {unassignedOrders.length === 0 && (
                <div className="px-6 py-4 text-center text-sm text-gray-500">
                  Alle Aufträge sind zugewiesen
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <AssignmentsTable />
        </div>
        <div className="lg:col-span-1">
          <OptimizationPanel />
        </div>
      </div>
    </div>
  );
};