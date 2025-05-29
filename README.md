# 🚛 Truck Dispatch Optimization System

A modern web application for optimizing truck-to-order assignments using linear programming.

## Features

- **🎯 Real-time Optimization**: Uses PuLP linear programming to optimize truck assignments
- **📊 Interactive Dashboard**: Modern React frontend with real-time metrics
- **🗺️ Geographic Visualization**: Map view with truck and order locations  
- **⚙️ Configurable Parameters**: Adjust optimization priorities for distance, time windows, and order priority
- **📈 Analysis & Reporting**: Detailed results with CSV export functionality
- **🔒 Assignment Locking**: Lock specific assignments and optimize around them

## Architecture

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Python + PuLP (Linear Programming) + Flask API  
- **Integration**: REST API connecting React UI to Python optimization engine

## Quick Start

### Option 1: One-Command Start (Recommended)

```bash
python start_local.py
```

This will:
- Check dependencies
- Start the API server (Flask) on http://localhost:5000
- Start the frontend (React) on http://localhost:5173  
- Open your browser automatically

### Option 2: Manual Start

#### 1. Install Dependencies

**Python packages:**
```bash
pip install pulp flask flask-cors
```

**Frontend packages:**
```bash
cd src/front
npm install --legacy-peer-deps
```

#### 2. Start API Server
```bash
cd src/api
python server.py
```

#### 3. Start Frontend (in new terminal)
```bash
cd src/front
npm run dev
```

#### 4. Open Browser
Navigate to http://localhost:5173

## Usage

1. **Dashboard View**: See current truck assignments and metrics
2. **Optimization Panel**: 
   - Adjust parameters (distance priority, time windows, order priority)
   - Click "Optimierung starten" to run optimization
   - View results in real-time
3. **Map View**: Geographic visualization of trucks and orders
4. **Analysis**: Detailed optimization results and performance metrics

## API Endpoints

- `POST /api/optimize` - Run optimization with current data
- `GET /api/status` - Health check
- `GET /api/results/latest` - Get latest optimization results

## Configuration

The system currently generates mock data for:
- **10 trucks** with realistic capacities and availability windows
- **15 orders** with priorities, time windows, and geographic locations

Production configuration supports:
- **200 trucks** 
- **300 orders**
- Real coordinate systems
- Integration with routing services

## Development

### Project Structure
```
├── src/
│   ├── front/          # React frontend
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── context/
│   │   │   └── data/
│   │   └── package.json
│   ├── api/            # Flask API server
│   │   └── server.py
│   └── dispo/          # Python optimization engine
│       └── dispo.py
├── start_local.py      # Development startup script
└── README.md
```

### Key Components

**Frontend:**
- `OptimizationPanel.tsx` - Main optimization controls
- `DataContext.tsx` - State management and API integration
- `Dashboard.tsx` - Main dashboard view

**Backend:**
- `server.py` - Flask API server with CORS
- `dispo.py` - PuLP linear programming optimization

## Technology Stack

**Frontend:**
- React 18.3.1 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Leaflet (maps)
- Recharts (data visualization)

**Backend:**
- Python 3.12+
- PuLP 3.2.1 (linear programming)
- Flask 2.3.2 (API server)
- CBC Solver (optimization engine)

## Output Files

The system generates timestamped CSV files in `src/dispo/optimierungs_ergebnisse_dispo/`:

- `rohdaten_lkw_*.csv` - Raw truck data
- `rohdaten_auftraege_*.csv` - Raw order data  
- `ergebnisse_zugewiesene_auftraege_*.csv` - Assigned orders with full details
- `ergebnisse_nicht_zugewiesene_auftraege_*.csv` - Unassigned orders
- `ergebnisse_lkw_auslastung_*.csv` - Truck utilization statistics

## Next Steps

- [ ] Real routing service integration (replace Euclidean distance)
- [ ] Authentication and user management
- [ ] Database persistence
- [ ] Real-time WebSocket updates
- [ ] Advanced constraint handling (truck properties, order requirements)
- [ ] Performance monitoring and analytics

## Troubleshooting

**API Connection Issues:**
- Ensure both frontend (port 5173) and API (port 5000) are running
- Check browser console for CORS errors
- Verify API status at http://localhost:5000/api/status

**Optimization Issues:**  
- Check that PuLP is properly installed: `python -c "import pulp; print('OK')"`
- Verify CBC solver is available (included with PuLP)
- Check API server logs for detailed error messages

**Frontend Issues:**
- Run `npm install --legacy-peer-deps` to resolve dependency conflicts
- Clear browser cache and reload
- Check browser console for JavaScript errors
