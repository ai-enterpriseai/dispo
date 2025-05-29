import React, { useState } from 'react';
import { useData } from '../../context/DataContext';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import { Truck, Package, MapPin } from 'lucide-react';
import { divIcon } from 'leaflet';
import { renderToString } from 'react-dom/server';
import 'leaflet/dist/leaflet.css';

// Fix the default icon issue
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

export const MapDisplay: React.FC = () => {
  const { trucks, orders, assignments } = useData();
  const [selectedTruckId, setSelectedTruckId] = useState<string | null>(null);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);

  const createTruckIcon = (status: string) => {
    const color = getTruckStatusColor(status);
    
    return divIcon({
      html: renderToString(
        <div className={`flex items-center justify-center rounded-full ${color} p-1 border-2 border-white`}>
          <Truck className="h-4 w-4" />
        </div>
      ),
      className: 'custom-div-icon',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
  };

  const createOrderIcon = (priority: number) => {
    const color = getOrderPriorityColor(priority);
    
    return divIcon({
      html: renderToString(
        <div className={`flex items-center justify-center rounded-full ${color} p-1 border-2 border-white`}>
          <Package className="h-4 w-4" />
        </div>
      ),
      className: 'custom-div-icon',
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });
  };

  const getTruckStatusColor = (status: string) => {
    switch (status) {
      case 'idle': return 'bg-gray-400 text-white';
      case 'loading': return 'bg-blue-500 text-white';
      case 'en-route': return 'bg-green-500 text-white';
      case 'delivering': return 'bg-purple-500 text-white';
      case 'maintenance': return 'bg-red-500 text-white';
      default: return 'bg-gray-400 text-white';
    }
  };

  const getOrderPriorityColor = (priority: number) => {
    switch (priority) {
      case 1: return 'bg-red-500 text-white';
      case 2: return 'bg-amber-500 text-white';
      case 3: return 'bg-green-500 text-white';
      default: return 'bg-gray-400 text-white';
    }
  };

  // Calculate center point of all trucks and orders
  const calculateCenter = () => {
    if (trucks.length === 0 && orders.length === 0) {
      return [50.0, 10.0]; // Default to central Germany
    }
    
    const allPoints = [
      ...trucks.map(truck => truck.location),
      ...orders.map(order => order.pickupLocation)
    ];
    
    const latSum = allPoints.reduce((sum, point) => sum + point.lat, 0);
    const lngSum = allPoints.reduce((sum, point) => sum + point.lng, 0);
    
    return [
      latSum / allPoints.length,
      lngSum / allPoints.length
    ];
  };

  const center = calculateCenter();

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

  const getTruckTypeText = (type: string) => {
    switch (type) {
      case 'small': return 'Klein';
      case 'medium': return 'Mittel';
      case 'large': return 'Groß';
      default: return type;
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

  return (
    <div className="h-full rounded-lg overflow-hidden shadow bg-white">
      <div className="relative h-full w-full">
        <MapContainer 
          center={[center[0], center[1]]} 
          zoom={5} 
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {/* Trucks */}
          {trucks.map(truck => (
            <Marker
              key={truck.id}
              position={[truck.location.lat, truck.location.lng]}
              icon={createTruckIcon(truck.status)}
              eventHandlers={{
                click: () => {
                  setSelectedTruckId(truck.id);
                  setSelectedOrderId(null);
                }
              }}
            >
              <Popup>
                <div className="p-1">
                  <h3 className="font-medium">{truck.name}</h3>
                  <p className="text-sm">Fahrer: {truck.driver}</p>
                  <p className="text-sm">Status: {getTruckStatusText(truck.status)}</p>
                  <p className="text-sm">Typ: {getTruckTypeText(truck.type)}</p>
                  <p className="text-sm">Kapazität: {truck.capacity.toLocaleString()} kg</p>
                  <p className="text-sm">Verfügbar: {truck.availableFrom.toFixed(2)} - {truck.availableTo.toFixed(2)} Uhr</p>
                </div>
              </Popup>
            </Marker>
          ))}
          
          {/* Orders */}
          {orders.map(order => (
            <Marker
              key={order.id}
              position={[order.pickupLocation.lat, order.pickupLocation.lng]}
              icon={createOrderIcon(order.priority)}
              eventHandlers={{
                click: () => {
                  setSelectedOrderId(order.id);
                  setSelectedTruckId(null);
                }
              }}
            >
              <Popup>
                <div className="p-1">
                  <h3 className="font-medium">{order.customer}</h3>
                  <p className="text-sm">{getOrderPriorityText(order.priority)}</p>
                  <p className="text-sm">Abholung: {order.pickupLocation.address}</p>
                  <p className="text-sm">Lieferung: {order.deliveryLocation.address}</p>
                  <p className="text-sm">Gewicht: {order.weight.toLocaleString()} kg</p>
                  <p className="text-sm">Ladezeit: {order.loadingDuration.toFixed(2)} Std.</p>
                  <p className="text-sm">Entladezeit: {order.unloadingDuration.toFixed(2)} Std.</p>
                </div>
              </Popup>
            </Marker>
          ))}
          
          {/* Draw lines for assignments */}
          {assignments.map(assignment => {
            const truck = trucks.find(t => t.id === assignment.truckId);
            const order = orders.find(o => o.id === assignment.orderId);
            
            if (!truck || !order) return null;
            
            const isSelected = (
              truck.id === selectedTruckId || 
              order.id === selectedOrderId
            );
            
            return (
              <Polyline
                key={assignment.id}
                positions={[
                  [truck.location.lat, truck.location.lng],
                  [order.pickupLocation.lat, order.pickupLocation.lng]
                ]}
                color={isSelected ? '#2563EB' : '#9CA3AF'}
                weight={isSelected ? 3 : 1.5}
                opacity={isSelected ? 0.8 : 0.4}
                dashArray={assignment.locked ? '' : '5, 5'}
              />
            );
          })}
        </MapContainer>
        
        <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-3 z-[1000]">
          <div className="text-sm font-medium">Kartenlegende</div>
          <div className="mt-2 space-y-1">
            <div className="flex items-center">
              <div className="w-5 h-5 flex items-center justify-center bg-gray-400 text-white rounded-full mr-2">
                <Truck className="h-3 w-3" />
              </div>
              <span className="text-xs">Inaktives Fahrzeug</span>
            </div>
            <div className="flex items-center">
              <div className="w-5 h-5 flex items-center justify-center bg-blue-500 text-white rounded-full mr-2">
                <Truck className="h-3 w-3" />
              </div>
              <span className="text-xs">Beladendes Fahrzeug</span>
            </div>
            <div className="flex items-center">
              <div className="w-5 h-5 flex items-center justify-center bg-green-500 text-white rounded-full mr-2">
                <Truck className="h-3 w-3" />
              </div>
              <span className="text-xs">Fahrendes Fahrzeug</span>
            </div>
            <div className="flex items-center">
              <div className="w-5 h-5 flex items-center justify-center bg-red-500 text-white rounded-full mr-2">
                <Package className="h-3 w-3" />
              </div>
              <span className="text-xs">Hohe Priorität</span>
            </div>
            <div className="flex items-center">
              <div className="w-5 h-5 flex items-center justify-center bg-amber-500 text-white rounded-full mr-2">
                <Package className="h-3 w-3" />
              </div>
              <span className="text-xs">Mittlere Priorität</span>
            </div>
            <div className="flex items-center">
              <div className="w-5 h-5 flex items-center justify-center bg-green-500 text-white rounded-full mr-2">
                <Package className="h-3 w-3" />
              </div>
              <span className="text-xs">Niedrige Priorität</span>
            </div>
            <div className="pt-1 border-t border-gray-200">
              <div className="flex items-center">
                <div className="w-5 h-0.5 bg-gray-400 mr-2"></div>
                <span className="text-xs">Fahrzeug-Auftrag Zuweisung</span>
              </div>
              <div className="flex items-center mt-1">
                <div className="w-5 h-0.5 bg-gray-400 border-dashed border-t border-gray-400 mr-2"></div>
                <span className="text-xs">Entsperrte Zuweisung</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};