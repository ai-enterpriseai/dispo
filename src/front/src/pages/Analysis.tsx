import React from 'react';
import { OptimizationResults } from '../components/analysis/OptimizationResults';

export const Analysis: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Analyse</h1>
      </div>

      <OptimizationResults />
    </div>
  );
};