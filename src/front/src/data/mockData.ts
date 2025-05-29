// Types
export interface Truck {
  id: string;
  name: string;
  type: 'small' | 'medium' | 'large';
  status: 'idle' | 'loading' | 'en-route' | 'delivering' | 'maintenance';
  location: {
    lat: number;
    lng: number;
  };
  capacity: number;
  driver: string;
  availableFrom: number; // in hours
  availableTo: number; // in hours
}

export interface Order {
  id: string;
  customer: string;
  priority: 1 | 2 | 3; // 1 = high, 2 = medium, 3 = low
  pickupLocation: {
    lat: number;
    lng: number;
    address: string;
  };
  deliveryLocation: {
    lat: number;
    lng: number;
    address: string;
  };
  timeWindow: {
    start: Date;
    end: Date;
  };
  size: number;
  status: 'pending' | 'assigned' | 'in-progress' | 'completed';
  loadingDuration: number; // in hours
  unloadingDuration: number; // in hours
  weight: number; // in kg
}

export interface Assignment {
  id: string;
  truckId: string;
  orderId: string;
  distance: number;
  estimatedArrival: Date;
  status: 'pending' | 'assigned' | 'in-progress' | 'completed';
  locked: boolean;
}

export interface OptimizationParameters {
  distancePriority: number;
  timeWindowPriority: number;
  orderPriorityWeight: number;
}

// German mock data for trucks based on the provided data
const germanTruckData = [
  { id: 'LKW1', location: [27.5, 22.32], capacity: 13000, availableFrom: 8.28, availableTo: 16.38 },
  { id: 'LKW2', location: [8.69, 42.19], capacity: 10000, availableFrom: 8.35, availableTo: 19.92 },
  { id: 'LKW3', location: [60.2, 56.12], capacity: 23000, availableFrom: 7.19, availableTo: 16.12 },
  { id: 'LKW4', location: [80.94, 0.65], capacity: 15000, availableFrom: 7.44, availableTo: 17.8 },
  { id: 'LKW5', location: [15.55, 95.72], capacity: 20000, availableFrom: 8.4, availableTo: 17.76 },
  { id: 'LKW6', location: [35.9, 34.4], capacity: 18000, availableFrom: 7.2, availableTo: 16.72 },
  { id: 'LKW7', location: [53.62, 97.31], capacity: 22000, availableFrom: 8.61, availableTo: 19.53 },
  { id: 'LKW8', location: [62.86, 88.55], capacity: 21000, availableFrom: 7.16, availableTo: 16.33 },
  { id: 'LKW9', location: [4.58, 22.79], capacity: 19000, availableFrom: 8.15, availableTo: 18.97 },
  { id: 'LKW10', location: [86.65, 38.01], capacity: 24000, availableFrom: 8.97, availableTo: 20.39 }
];

// German mock data for orders based on the provided data
const germanOrderData = [
  { id: 'AUF1', pickup: [26.7, 93.67], delivery: [64.8, 60.91], weight: 2600, loadTimeEarly: 11.81, loadTimeLate: 13.44, loadDuration: 0.86, unloadDuration: 0.87, priority: 3 },
  { id: 'AUF2', pickup: [64.0, 55.69], delivery: [68.46, 84.29], weight: 10400, loadTimeEarly: 12.37, loadTimeLate: 16.34, loadDuration: 0.66, unloadDuration: 0.88, priority: 1 },
  { id: 'AUF3', pickup: [21.1, 94.29], delivery: [87.64, 31.47], weight: 8800, loadTimeEarly: 9.37, loadTimeLate: 11.17, loadDuration: 0.53, unloadDuration: 0.82, priority: 2 },
  { id: 'AUF4', pickup: [24.66, 56.14], delivery: [26.27, 58.46], weight: 11900, loadTimeEarly: 10.37, loadTimeLate: 12.47, loadDuration: 1.41, unloadDuration: 0.96, priority: 3 },
  { id: 'AUF5', pickup: [9.09, 4.71], delivery: [10.96, 62.74], weight: 10600, loadTimeEarly: 10.4, loadTimeLate: 12.93, loadDuration: 0.72, unloadDuration: 1.5, priority: 3 },
  { id: 'AUF6', pickup: [52.91, 97.11], delivery: [86.08, 1.15], weight: 9700, loadTimeEarly: 10.53, loadTimeLate: 14.52, loadDuration: 0.56, unloadDuration: 0.88, priority: 1 },
  { id: 'AUF7', pickup: [11.16, 43.48], delivery: [45.37, 95.38], weight: 11700, loadTimeEarly: 12.09, loadTimeLate: 15.03, loadDuration: 1.04, unloadDuration: 0.77, priority: 3 },
  { id: 'AUF8', pickup: [87.05, 29.84], delivery: [63.89, 60.9], weight: 2400, loadTimeEarly: 9.58, loadTimeLate: 13.32, loadDuration: 1, unloadDuration: 0.68, priority: 2 },
  { id: 'AUF9', pickup: [0.06, 32.42], delivery: [1.95, 92.91], weight: 11700, loadTimeEarly: 12.58, loadTimeLate: 15.19, loadDuration: 1.04, unloadDuration: 1.28, priority: 2 },
  { id: 'AUF10', pickup: [73.19, 81.6], delivery: [97.8, 53.27], weight: 2100, loadTimeEarly: 9.44, loadTimeLate: 10.68, loadDuration: 0.74, unloadDuration: 1.07, priority: 1 },
  { id: 'AUF11', pickup: [60.66, 96.44], delivery: [92.89, 75.53], weight: 9300, loadTimeEarly: 11.96, loadTimeLate: 14.76, loadDuration: 1.45, unloadDuration: 0.67, priority: 1 },
  { id: 'AUF12', pickup: [89.96, 45.15], delivery: [24.79, 6.4], weight: 700, loadTimeEarly: 12.28, loadTimeLate: 14.4, loadDuration: 0.9, unloadDuration: 1.17, priority: 3 },
  { id: 'AUF13', pickup: [5.89, 6.74], delivery: [3.14, 33.04], weight: 7000, loadTimeEarly: 11.32, loadTimeLate: 14.47, loadDuration: 1.09, unloadDuration: 0.51, priority: 1 },
  { id: 'AUF14', pickup: [88.24, 57.62], delivery: [24.3, 47.3], weight: 5700, loadTimeEarly: 9.67, loadTimeLate: 12.84, loadDuration: 0.99, unloadDuration: 1.04, priority: 1 },
  { id: 'AUF15', pickup: [86.38, 5.42], delivery: [65.35, 64.62], weight: 1200, loadTimeEarly: 8.57, loadTimeLate: 10.9, loadDuration: 1.16, unloadDuration: 0.85, priority: 2 }
];

// Helper functions to generate mock data with German data
export const generateMockTrucks = (count: number): Truck[] => {
  // If count is less than or equal to the provided German truck data, use only the provided data
  if (count <= germanTruckData.length) {
    return germanTruckData.slice(0, count).map((truck, index) => {
      const truckTypes: ('small' | 'medium' | 'large')[] = ['small', 'medium', 'large'];
      const truckStatus: ('idle' | 'loading' | 'en-route' | 'delivering' | 'maintenance')[] = 
        ['idle', 'loading', 'en-route', 'delivering', 'maintenance'];
      const type = truck.capacity <= 15000 ? 'small' : truck.capacity <= 20000 ? 'medium' : 'large';
      
      return {
        id: truck.id,
        name: `Fahrzeug ${index + 1}`,
        type,
        status: truckStatus[Math.floor(Math.random() * truckStatus.length)],
        location: {
          lat: truck.location[0],
          lng: truck.location[1]
        },
        capacity: truck.capacity,
        driver: `Fahrer ${index + 1}`,
        availableFrom: truck.availableFrom,
        availableTo: truck.availableTo
      };
    });
  }
  
  // If more trucks are needed than provided, use the German data first, then fill with random data
  const trucks: Truck[] = germanTruckData.map((truck, index) => {
    const truckTypes: ('small' | 'medium' | 'large')[] = ['small', 'medium', 'large'];
    const truckStatus: ('idle' | 'loading' | 'en-route' | 'delivering' | 'maintenance')[] = 
      ['idle', 'loading', 'en-route', 'delivering', 'maintenance'];
    const type = truck.capacity <= 15000 ? 'small' : truck.capacity <= 20000 ? 'medium' : 'large';
    
    return {
      id: truck.id,
      name: `Fahrzeug ${index + 1}`,
      type,
      status: truckStatus[Math.floor(Math.random() * truckStatus.length)],
      location: {
        lat: truck.location[0],
        lng: truck.location[1]
      },
      capacity: truck.capacity,
      driver: `Fahrer ${index + 1}`,
      availableFrom: truck.availableFrom,
      availableTo: truck.availableTo
    };
  });
  
  // Generate additional random trucks if needed
  for (let i = germanTruckData.length; i < count; i++) {
    const truckTypes: ('small' | 'medium' | 'large')[] = ['small', 'medium', 'large'];
    const truckStatus: ('idle' | 'loading' | 'en-route' | 'delivering' | 'maintenance')[] = 
      ['idle', 'loading', 'en-route', 'delivering', 'maintenance'];
    const type = truckTypes[Math.floor(Math.random() * truckTypes.length)];
    
    trucks.push({
      id: `LKW${i + 1}`,
      name: `Fahrzeug ${i + 1}`,
      type,
      status: truckStatus[Math.floor(Math.random() * truckStatus.length)],
      location: {
        lat: 40 + (Math.random() * 20 - 10),
        lng: 40 + (Math.random() * 20 - 10)
      },
      capacity: type === 'small' ? 10000 : type === 'medium' ? 20000 : 30000,
      driver: `Fahrer ${i + 1}`,
      availableFrom: 7 + Math.random() * 2,
      availableTo: 16 + Math.random() * 4
    });
  }
  
  return trucks;
};

export const generateMockOrders = (count: number): Order[] => {
  // If count is less than or equal to the provided German order data, use only the provided data
  if (count <= germanOrderData.length) {
    return germanOrderData.slice(0, count).map((order, index) => {
      // Convert hour-based time to Date objects
      const now = new Date();
      const startHours = Math.floor(order.loadTimeEarly);
      const startMinutes = Math.floor((order.loadTimeEarly % 1) * 60);
      const endHours = Math.floor(order.loadTimeLate);
      const endMinutes = Math.floor((order.loadTimeLate % 1) * 60);
      
      const start = new Date(now);
      start.setHours(startHours, startMinutes, 0, 0);
      
      const end = new Date(now);
      end.setHours(endHours, endMinutes, 0, 0);
      
      return {
        id: order.id,
        customer: `Kunde ${index + 1}`,
        priority: order.priority as 1 | 2 | 3,
        pickupLocation: {
          lat: order.pickup[0],
          lng: order.pickup[1],
          address: `Abholort ${index + 1}`
        },
        deliveryLocation: {
          lat: order.delivery[0],
          lng: order.delivery[1],
          address: `Lieferort ${index + 1}`
        },
        timeWindow: {
          start,
          end
        },
        size: Math.ceil(order.weight / 1000), // Convert weight to size units
        status: ['pending', 'assigned', 'in-progress', 'completed'][Math.floor(Math.random() * 4)] as 'pending' | 'assigned' | 'in-progress' | 'completed',
        loadingDuration: order.loadDuration,
        unloadingDuration: order.unloadDuration,
        weight: order.weight
      };
    });
  }
  
  // If more orders are needed than provided, use the German data first, then fill with random data
  const orders: Order[] = germanOrderData.map((order, index) => {
    // Convert hour-based time to Date objects
    const now = new Date();
    const startHours = Math.floor(order.loadTimeEarly);
    const startMinutes = Math.floor((order.loadTimeEarly % 1) * 60);
    const endHours = Math.floor(order.loadTimeLate);
    const endMinutes = Math.floor((order.loadTimeLate % 1) * 60);
    
    const start = new Date(now);
    start.setHours(startHours, startMinutes, 0, 0);
    
    const end = new Date(now);
    end.setHours(endHours, endMinutes, 0, 0);
    
    return {
      id: order.id,
      customer: `Kunde ${index + 1}`,
      priority: order.priority as 1 | 2 | 3,
      pickupLocation: {
        lat: order.pickup[0],
        lng: order.pickup[1],
        address: `Abholort ${index + 1}`
      },
      deliveryLocation: {
        lat: order.delivery[0],
        lng: order.delivery[1],
        address: `Lieferort ${index + 1}`
      },
      timeWindow: {
        start,
        end
      },
      size: Math.ceil(order.weight / 1000), // Convert weight to size units
      status: ['pending', 'assigned', 'in-progress', 'completed'][Math.floor(Math.random() * 4)] as 'pending' | 'assigned' | 'in-progress' | 'completed',
      loadingDuration: order.loadDuration,
      unloadingDuration: order.unloadDuration,
      weight: order.weight
    };
  });
  
  // Generate additional random orders if needed
  for (let i = germanOrderData.length; i < count; i++) {
    const priorities: (1 | 2 | 3)[] = [1, 2, 3];
    const statuses: ('pending' | 'assigned' | 'in-progress' | 'completed')[] = 
      ['pending', 'assigned', 'in-progress', 'completed'];
    
    // Random time window within the next 24 hours
    const startTime = new Date(Date.now() + Math.random() * 3600000 * 24); // Up to 24 hours from now
    const endTime = new Date(startTime.getTime() + Math.random() * 3600000 * 4); // 0-4 hours after start
    
    // Base location around central area
    const baseLat = 50;
    const baseLng = 50;
    
    // Pickup location
    const pickupLat = baseLat + (Math.random() * 40 - 20);
    const pickupLng = baseLng + (Math.random() * 40 - 20);
    
    // Delivery location (some distance away from pickup)
    const deliveryLat = pickupLat + (Math.random() * 20 - 10);
    const deliveryLng = pickupLng + (Math.random() * 20 - 10);
    
    orders.push({
      id: `AUF${i + 1}`,
      customer: `Kunde ${i + 1}`,
      priority: priorities[Math.floor(Math.random() * priorities.length)],
      pickupLocation: {
        lat: pickupLat,
        lng: pickupLng,
        address: `Abholort ${i + 1}`
      },
      deliveryLocation: {
        lat: deliveryLat,
        lng: deliveryLng,
        address: `Lieferort ${i + 1}`
      },
      timeWindow: {
        start: startTime,
        end: endTime
      },
      size: Math.floor(Math.random() * 15) + 1, // 1-15 size units
      status: statuses[Math.floor(Math.random() * statuses.length)],
      loadingDuration: 0.5 + Math.random() * 1, // 0.5-1.5 hours
      unloadingDuration: 0.5 + Math.random() * 1, // 0.5-1.5 hours
      weight: (Math.floor(Math.random() * 15) + 1) * 1000 // 1000-15000 kg
    });
  }
  
  return orders;
};