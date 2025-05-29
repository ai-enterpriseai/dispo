import React from 'react';
import { MapDisplay } from '../components/map/MapDisplay';

export const MapView: React.FC = () => {
  return (
    <div className="space-y-6 h-[calc(100vh-9rem)]">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Kartenansicht</h1>
      </div>

      <div className="h-full">
        <MapDisplay />
      </div>
    </div>
  );
};