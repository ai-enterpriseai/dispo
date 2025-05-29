import React, { useState } from 'react';
import { useData } from '../../context/DataContext';
import { Lock, Unlock, MapPin, Calendar, Truck } from 'lucide-react';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';

export const AssignmentsTable: React.FC = () => {
  const { trucks, orders, assignments, lockAssignment } = useData();
  const [sortField, setSortField] = useState<string>('distance');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filter, setFilter] = useState<string>('');

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedAssignments = [...assignments].sort((a, b) => {
    let comparison = 0;
    
    switch (sortField) {
      case 'truck':
        const truckA = trucks.find(t => t.id === a.truckId)?.name || '';
        const truckB = trucks.find(t => t.id === b.truckId)?.name || '';
        comparison = truckA.localeCompare(truckB);
        break;
      case 'order':
        const orderA = orders.find(o => o.id === a.orderId)?.customer || '';
        const orderB = orders.find(o => o.id === b.orderId)?.customer || '';
        comparison = orderA.localeCompare(orderB);
        break;
      case 'distance':
        comparison = a.distance - b.distance;
        break;
      case 'arrival':
        comparison = a.estimatedArrival.getTime() - b.estimatedArrival.getTime();
        break;
      case 'status':
        comparison = a.status.localeCompare(b.status);
        break;
      default:
        comparison = 0;
    }
    
    return sortDirection === 'asc' ? comparison : -comparison;
  });

  const filteredAssignments = sortedAssignments.filter(assignment => {
    if (!filter) return true;
    
    const truck = trucks.find(t => t.id === assignment.truckId);
    const order = orders.find(o => o.id === assignment.orderId);
    
    const filterLower = filter.toLowerCase();
    
    return (
      truck?.name.toLowerCase().includes(filterLower) ||
      order?.customer.toLowerCase().includes(filterLower) ||
      assignment.status.toLowerCase().includes(filterLower)
    );
  });

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

  const getOrderPriorityColor = (priority: number) => {
    switch (priority) {
      case 1: return 'bg-red-100 text-red-800';
      case 2: return 'bg-amber-100 text-amber-800';
      case 3: return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

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

  const getOrderPriorityText = (priority: number) => {
    switch (priority) {
      case 1: return 'Priorität 1';
      case 2: return 'Priorität 2';
      case 3: return 'Priorität 3';
      default: return `Priorität ${priority}`;
    }
  };

  const getAssignmentStatusText = (status: string) => {
    switch (status) {
      case 'pending': return 'Ausstehend';
      case 'assigned': return 'Zugewiesen';
      case 'in-progress': return 'In Bearbeitung';
      case 'completed': return 'Abgeschlossen';
      default: return status;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200 flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-2 sm:space-y-0">
        <h2 className="text-lg font-medium text-gray-900">Aktuelle Zuweisungen</h2>
        <div className="flex items-center">
          <input
            type="text"
            placeholder="Zuweisungen filtern..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort('truck')}
              >
                <div className="flex items-center">
                  Fahrzeug
                  {sortField === 'truck' && (
                    <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort('order')}
              >
                <div className="flex items-center">
                  Auftrag
                  {sortField === 'order' && (
                    <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort('distance')}
              >
                <div className="flex items-center">
                  Entfernung
                  {sortField === 'distance' && (
                    <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort('arrival')}
              >
                <div className="flex items-center">
                  Geschätzte Ankunft
                  {sortField === 'arrival' && (
                    <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort('status')}
              >
                <div className="flex items-center">
                  Status
                  {sortField === 'status' && (
                    <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </div>
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Sperre
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredAssignments.length > 0 ? (
              filteredAssignments.map((assignment) => {
                const truck = trucks.find(t => t.id === assignment.truckId);
                const order = orders.find(o => o.id === assignment.orderId);
                
                if (!truck || !order) return null;
                
                return (
                  <tr key={assignment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center rounded-full bg-blue-100 text-blue-700">
                          <Truck className="h-5 w-5" />
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">{truck.name}</div>
                          <div className="text-sm text-gray-500">{truck.driver}</div>
                        </div>
                      </div>
                      <div className="mt-1">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getTruckStatusColor(truck.status)}`}>
                          {getTruckStatusText(truck.status)}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="ml-0">
                          <div className="text-sm font-medium text-gray-900">{order.customer}</div>
                          <div className="text-sm text-gray-500 flex items-center">
                            <MapPin className="h-3 w-3 mr-1" />
                            {order.pickupLocation.address.substring(0, 20)}...
                          </div>
                        </div>
                      </div>
                      <div className="mt-1 flex items-center">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getOrderPriorityColor(order.priority)}`}>
                          {getOrderPriorityText(order.priority)}
                        </span>
                        <span className="ml-2 text-xs text-gray-500 flex items-center">
                          <Calendar className="h-3 w-3 mr-1" />
                          {format(order.timeWindow.start, 'HH:mm', { locale: de })} - {format(order.timeWindow.end, 'HH:mm', { locale: de })}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {assignment.distance.toLocaleString()} km
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(assignment.estimatedArrival, 'dd. MMM, HH:mm', { locale: de })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        {getAssignmentStatusText(assignment.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button
                        onClick={() => lockAssignment(assignment.id, !assignment.locked)}
                        className={`p-1 rounded-full ${
                          assignment.locked
                            ? 'text-amber-500 hover:text-amber-600'
                            : 'text-gray-400 hover:text-gray-500'
                        }`}
                      >
                        {assignment.locked ? <Lock className="h-5 w-5" /> : <Unlock className="h-5 w-5" />}
                      </button>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">
                  Keine Zuweisungen gefunden
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="px-6 py-4 border-t border-gray-200">
        <p className="text-sm text-gray-500">
          Zeige {filteredAssignments.length} von {assignments.length} Zuweisungen
        </p>
      </div>
    </div>
  );
};