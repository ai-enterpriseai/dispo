import React from 'react';

function AppSimple() {
  console.log('Simple App component rendering...');
  
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1 style={{ color: 'blue' }}>🚛 Truck Dispatch Optimization System</h1>
      <p>If you can see this, React is working!</p>
      <div style={{ 
        backgroundColor: '#f0f0f0', 
        padding: '10px', 
        marginTop: '20px', 
        borderRadius: '5px' 
      }}>
        <h2>System Status:</h2>
        <ul>
          <li>✅ React rendering works</li>
          <li>✅ Basic styling works</li>
          <li>🔄 Testing components...</li>
        </ul>
      </div>
    </div>
  );
}

export default AppSimple; 