import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { DataProvider } from './context/DataContext';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { MapView } from './pages/MapView';
import { Analysis } from './pages/Analysis';
import { Settings } from './pages/Settings';

function App() {
  console.log('App component rendering...');
  
  try {
    return (
      <DataProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/map" element={<MapView />} />
              <Route path="/analysis" element={<Analysis />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </Router>
      </DataProvider>
    );
  } catch (error) {
    console.error('Error in App component:', error);
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <h1>Error loading application</h1>
        <p>Check the browser console for details.</p>
        <pre>{String(error)}</pre>
      </div>
    );
  }
}

export default App;