import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { 
  Truck, 
  Order, 
  Assignment, 
  OptimizationParameters, 
  generateMockTrucks, 
  generateMockOrders 
} from '../data/mockData';

// API Configuration - Use relative URLs for single service deployment
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

interface DataContextType {
  trucks: Truck[];
  orders: Order[];
  assignments: Assignment[];
  optimizationParameters: OptimizationParameters;
  isOptimizing: boolean;
  lastUpdated: Date;
  lastOptimized: Date | null;
  fleetUtilization: number;
  totalDistance: number;
  unassignedOrders: number;
  updateAssignment: (truckId: string, orderId: string) => void;
  lockAssignment: (assignmentId: string, locked: boolean) => void;
  runOptimization: () => Promise<void>;
  updateOptimizationParameters: (params: Partial<OptimizationParameters>) => void;
  refreshData: () => Promise<void>;
  exportData: () => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const useData = () => {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};

interface DataProviderProps {
  children: ReactNode;
}

export const DataProvider: React.FC<DataProviderProps> = ({ children }) => {
  const [trucks, setTrucks] = useState<Truck[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [lastOptimized, setLastOptimized] = useState<Date | null>(null);
  const [isLoadingInitialData, setIsLoadingInitialData] = useState<boolean>(false);
  
  const [optimizationParameters, setOptimizationParameters] = useState<OptimizationParameters>({
    distancePriority: 0.5,
    timeWindowPriority: 0.3,
    orderPriorityWeight: 0.2
  });

  // Load initial data from backend
  const loadInitialData = async () => {
    if (isLoadingInitialData) {
      console.log('Already loading initial data, skipping...');
      return;
    }
    
    setIsLoadingInitialData(true);
    
    try {
      console.log('=== LOADING INITIAL DATA ===');
      console.log('Loading raw unassigned data from backend...');
      
      // Call the generate-data endpoint to get fresh unassigned data
      const generateResponse = await fetch(`${API_BASE_URL}/api/generate-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('Generate response status:', generateResponse.status);
      
      if (generateResponse.ok) {
        const generateResult = await generateResponse.json();
        console.log('Generate result:', generateResult);
        
        if (generateResult.status === 'success' && generateResult.data) {
          console.log('=== LOADED RAW DATA ===');
          console.log('Trucks:', generateResult.data.trucks?.length || 0);
          console.log('Orders:', generateResult.data.orders?.length || 0);
          console.log('Assignments:', generateResult.data.assignments?.length || 0);
          
          // Validate and set trucks with proper types
          const validatedTrucks = generateResult.data.trucks?.map((truck: any) => ({
            ...truck,
            status: (['idle', 'loading', 'en-route', 'delivering', 'maintenance'] as const).includes(truck.status) 
              ? truck.status as 'idle' | 'loading' | 'en-route' | 'delivering' | 'maintenance'
              : 'idle' as const
          })) || [];
          
          console.log('=== SETTING STATE ===');
          console.log('Validated trucks:', validatedTrucks.length);
          console.log('Orders:', generateResult.data.orders?.length || 0);
          console.log('Assignments:', generateResult.data.assignments?.length || 0);
          
          setTrucks(validatedTrucks);
          setOrders(generateResult.data.orders || []);
          setAssignments(generateResult.data.assignments || []);
          
          console.log('=== STATE SET SUCCESSFULLY ===');
          return; // Successfully loaded raw data
        } else {
          console.error('Generate result status not success or no data:', generateResult);
        }
      } else {
        console.error('Generate response not ok:', generateResponse.status, await generateResponse.text());
      }
      
      console.error('Failed to generate raw data, using mock data fallback');
      // Fallback to minimal mock data if backend is unavailable
      const mockTrucks = generateMockTrucks(10);
      const mockOrders = generateMockOrders(15);
      
      console.log('Using mock fallback - trucks:', mockTrucks.length, 'orders:', mockOrders.length);
      setTrucks(mockTrucks);
      setOrders(mockOrders);
      setAssignments([]);
      
    } catch (error) {
      console.error('API call error, using mock data:', error);
      // Fallback to minimal mock data if backend is unavailable
      const mockTrucks = generateMockTrucks(10);
      const mockOrders = generateMockOrders(15);
      
      console.log('Using mock fallback due to error - trucks:', mockTrucks.length, 'orders:', mockOrders.length);
      setTrucks(mockTrucks);
      setOrders(mockOrders);
      setAssignments([]);
    } finally {
      setIsLoadingInitialData(false);
    }
  };

  // Initialize with backend data instead of mock data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Debug state changes
  useEffect(() => {
    console.log('=== STATE CHANGE DEBUG ===');
    console.log('Current state:');
    console.log('  - Trucks:', trucks.length, trucks.map(t => `${t.id}:${t.status}`));
    console.log('  - Orders:', orders.length, orders.map(o => `${o.id}:${o.status}`));
    console.log('  - Assignments:', assignments.length);
  }, [trucks, orders, assignments]);

  // Calculate metrics
  const fleetUtilization = trucks.length > 0 
    ? (assignments.length / trucks.length) * 100 
    : 0;
    
  const totalDistance = assignments.reduce((sum, assignment) => sum + assignment.distance, 0);
  
  const unassignedOrders = orders.length - assignments.length;

  // Update an assignment
  const updateAssignment = (truckId: string, orderId: string) => {
    // First check if the order is already assigned
    const existingAssignmentIndex = assignments.findIndex(a => a.orderId === orderId);
    
    if (existingAssignmentIndex !== -1) {
      // Update the existing assignment
      const updatedAssignments = [...assignments];
      updatedAssignments[existingAssignmentIndex] = {
        ...updatedAssignments[existingAssignmentIndex],
        truckId,
        // Recalculate distance
        distance: calculateDistance(
          trucks.find(t => t.id === truckId)?.location,
          orders.find(o => o.id === orderId)?.pickupLocation
        ),
        estimatedArrival: new Date(Date.now() + Math.random() * 3600000 * 12),
      };
      setAssignments(updatedAssignments);
    } else {
      // Create a new assignment
      const newAssignment: Assignment = {
        id: `assignment-${Date.now()}`,
        truckId,
        orderId,
        distance: calculateDistance(
          trucks.find(t => t.id === truckId)?.location,
          orders.find(o => o.id === orderId)?.pickupLocation
        ),
        estimatedArrival: new Date(Date.now() + Math.random() * 3600000 * 12),
        status: 'assigned',
        locked: false
      };
      setAssignments([...assignments, newAssignment]);
    }
  };

  // Helper to calculate distance
  const calculateDistance = (
    truckLocation?: { lat: number; lng: number },
    orderLocation?: { lat: number; lng: number }
  ) => {
    if (!truckLocation || !orderLocation) return 0;
    
    return Math.round(
      Math.sqrt(
        Math.pow(truckLocation.lat - orderLocation.lat, 2) +
        Math.pow(truckLocation.lng - orderLocation.lng, 2)
      ) * 100
    );
  };

  // Lock/unlock an assignment
  const lockAssignment = (assignmentId: string, locked: boolean) => {
    setAssignments(
      assignments.map(assignment => 
        assignment.id === assignmentId 
          ? { ...assignment, locked } 
          : assignment
      )
    );
  };

  // Run the optimization algorithm
  const runOptimization = async () => {
    setIsOptimizing(true);
    
    try {
      console.log('Starting optimization with current data:', {
        trucks: trucks.length,
        orders: orders.length,
        assignments: assignments.length
      });
      
      // Call the real backend API
      const response = await fetch(`${API_BASE_URL}/api/optimize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          trucks: trucks,
          orders: orders,
          parameters: optimizationParameters,
          lockedAssignments: assignments.filter(a => a.locked)
        })
      });
      
      console.log('API Response status:', response.status);
      const result = await response.json();
      console.log('API Response data:', result);
      
      if (result.status === 'success' && result.data) {
        console.log('Updating state with backend data:', {
          trucks: result.data.trucks?.length,
          orders: result.data.orders?.length,
          assignments: result.data.assignments?.length
        });
        
        // Update with real optimization results
        const validatedTrucks = result.data.trucks?.map((truck: any) => ({
          ...truck,
          status: (['idle', 'loading', 'en-route', 'delivering', 'maintenance'] as const).includes(truck.status) 
            ? truck.status as 'idle' | 'loading' | 'en-route' | 'delivering' | 'maintenance'
            : 'idle' as const
        })) || [];
        
        setTrucks(validatedTrucks);
        setOrders(result.data.orders);
        setAssignments(result.data.assignments);
        setLastOptimized(new Date());
        console.log('Optimization completed successfully:', result.message);
        console.log('State should now be updated with backend data');
      } else {
        console.error('Optimization failed:', result.message);
        // Fall back to mock optimization if API fails
        await mockOptimization();
      }
    } catch (error) {
      console.error('API call failed:', error);
      // Fall back to mock optimization if API fails
      await mockOptimization();
    } finally {
      setIsOptimizing(false);
    }
  };

  // Fallback mock optimization (original implementation)
  const mockOptimization = async () => {
    // Simulate optimization delay
    await new Promise(resolve => setTimeout(resolve, 2500));
    
    // Get unlocked assignments and unassigned orders
    const lockedAssignments = assignments.filter(a => a.locked);
    const unlockedAssignmentOrderIds = assignments
      .filter(a => !a.locked)
      .map(a => a.orderId);
      
    const unassignedOrderIds = orders
      .filter(o => !assignments.some(a => a.orderId === o.id))
      .map(o => o.id);
      
    const availableTruckIds = trucks
      .filter(t => !lockedAssignments.some(a => a.truckId === t.id))
      .map(t => t.id);
    
    // Create new optimized assignments
    const newAssignments: Assignment[] = [...lockedAssignments];
    
    // Combine unassigned and unlocked orders
    const ordersToAssign = [...unlockedAssignmentOrderIds, ...unassignedOrderIds];
    
    // Simple greedy algorithm for demo purposes
    for (const orderId of ordersToAssign) {
      if (availableTruckIds.length === 0) break;
      
      const order = orders.find(o => o.id === orderId);
      if (!order) continue;
      
      // Find the closest available truck
      let closestTruckId = availableTruckIds[0];
      let minDistance = Number.MAX_VALUE;
      
      for (const truckId of availableTruckIds) {
        const truck = trucks.find(t => t.id === truckId);
        if (!truck) continue;
        
        const distance = calculateDistance(truck.location, order.pickupLocation);
        
        // Apply optimization parameters
        const timeWindowFactor = 1 - (optimizationParameters.timeWindowPriority * Math.random());
        const priorityFactor = 1 - (optimizationParameters.orderPriorityWeight * (order.priority / 3));
        const distanceFactor = optimizationParameters.distancePriority;
        
        const adjustedDistance = distance * distanceFactor * timeWindowFactor * priorityFactor;
        
        if (adjustedDistance < minDistance) {
          minDistance = adjustedDistance;
          closestTruckId = truckId;
        }
      }
      
      // Create assignment
      newAssignments.push({
        id: `assignment-${Date.now()}-${Math.random()}`,
        truckId: closestTruckId,
        orderId,
        distance: calculateDistance(
          trucks.find(t => t.id === closestTruckId)?.location,
          order.pickupLocation
        ),
        estimatedArrival: new Date(Date.now() + Math.random() * 3600000 * 12),
        status: 'assigned',
        locked: false
      });
      
      // Remove assigned truck from available trucks
      const truckIndex = availableTruckIds.indexOf(closestTruckId);
      availableTruckIds.splice(truckIndex, 1);
    }
    
    setAssignments(newAssignments);
    setLastOptimized(new Date());
  };

  // Update optimization parameters
  const updateOptimizationParameters = (params: Partial<OptimizationParameters>) => {
    setOptimizationParameters({ ...optimizationParameters, ...params });
  };

  // Refresh data from source systems
  const refreshData = async () => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // For demo, we'll just regenerate some of the mock data
    const updatedTrucks = trucks.map(truck => ({
      ...truck,
      location: {
        lat: truck.location.lat + (Math.random() * 0.02 - 0.01),
        lng: truck.location.lng + (Math.random() * 0.02 - 0.01)
      },
      status: Math.random() > 0.8 
        ? (['idle', 'loading', 'en-route', 'delivering'] as const)[Math.floor(Math.random() * 4)] as 'idle' | 'loading' | 'en-route' | 'delivering' | 'maintenance'
        : truck.status
    }));
    
    setTrucks(updatedTrucks);
    setLastUpdated(new Date());
  };

  // Export data
  const exportData = () => {
    const data = {
      trucks,
      orders,
      assignments,
      metrics: {
        fleetUtilization,
        totalDistance,
        unassignedOrders
      },
      lastUpdated,
      lastOptimized
    };
    
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `dispatch-optimization-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const value = {
    trucks,
    orders,
    assignments,
    optimizationParameters,
    isOptimizing,
    lastUpdated,
    lastOptimized,
    fleetUtilization,
    totalDistance,
    unassignedOrders,
    updateAssignment,
    lockAssignment,
    runOptimization,
    updateOptimizationParameters,
    refreshData,
    exportData
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};