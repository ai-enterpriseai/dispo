#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Server for Truck Dispatch Optimization System
Connects React frontend to Python optimization backend
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import subprocess
import json
import os
import csv
import io
from datetime import datetime
import sys

app = Flask(__name__, static_folder='../front/dist', static_url_path='')

# Enhanced CORS configuration for better browser compatibility
CORS(app, 
     origins=["http://localhost:5173", "http://127.0.0.1:5173"],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=True
)

def parse_csv_to_dict(csv_content):
    """Parse CSV content and return as list of dictionaries"""
    if not csv_content.strip():
        return []
    
    reader = csv.DictReader(io.StringIO(csv_content))
    return list(reader)

def get_latest_results():
    """Get the latest optimization results from CSV files"""
    # Use absolute path resolution
    current_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(current_dir, "..", "dispo", "optimierungs_ergebnisse_dispo")
    results_dir = os.path.abspath(results_dir)
    
    print(f"DEBUG get_latest_results: Looking for results in: {results_dir}") # DEBUG
    
    if not os.path.exists(results_dir):
        print(f"DEBUG get_latest_results: Results directory does not exist: {results_dir}") # DEBUG
        return None
    
    # Find the latest timestamp files
    files = []
    try:
        files = os.listdir(results_dir)
    except OSError as e:
        print(f"DEBUG get_latest_results: Error listing results_dir '{results_dir}': {e}") # DEBUG
        return None
        
    print(f"DEBUG get_latest_results: Found files in '{results_dir}': {files}") # DEBUG
    timestamps = set()
    
    for file in files:
        if '_' in file and file.endswith('.csv'):
            parts = file.split('_')
            if len(parts) >= 3:
                timestamp = f"{parts[-2]}_{parts[-1].replace('.csv', '')}"
                timestamps.add(timestamp)
    
    if not timestamps:
        print(f"DEBUG get_latest_results: No timestamp files found in {results_dir} among files: {files}") # DEBUG
        return None
    
    latest_timestamp = max(timestamps)
    print(f"DEBUG get_latest_results: Using latest timestamp: {latest_timestamp}") # DEBUG
    
    # Read all result files for the latest timestamp
    results = {}
    
    try:
        # Assigned orders
        assigned_file = f"ergebnisse_zugewiesene_auftraege_{latest_timestamp}.csv"
        assigned_path = os.path.join(results_dir, assigned_file)
        print(f"Looking for assigned orders file: {assigned_path}")
        if os.path.exists(assigned_path):
            with open(assigned_path, 'r', encoding='utf-8') as f:
                results['assigned_orders'] = parse_csv_to_dict(f.read())
                print(f"Loaded {len(results['assigned_orders'])} assigned orders")
        
        # Unassigned orders
        unassigned_file = f"ergebnisse_nicht_zugewiesene_auftraege_{latest_timestamp}.csv"
        unassigned_path = os.path.join(results_dir, unassigned_file)
        if os.path.exists(unassigned_path):
            with open(unassigned_path, 'r', encoding='utf-8') as f:
                results['unassigned_orders'] = parse_csv_to_dict(f.read())
                print(f"Loaded {len(results['unassigned_orders'])} unassigned orders")
        
        # Truck utilization
        truck_util_file = f"ergebnisse_lkw_auslastung_{latest_timestamp}.csv"
        truck_util_path = os.path.join(results_dir, truck_util_file)
        if os.path.exists(truck_util_path):
            with open(truck_util_path, 'r', encoding='utf-8') as f:
                results['truck_utilization'] = parse_csv_to_dict(f.read())
                print(f"Loaded {len(results['truck_utilization'])} truck utilization records")
        
        # Raw data
        raw_trucks_file = f"rohdaten_lkw_{latest_timestamp}.csv"
        raw_trucks_path = os.path.join(results_dir, raw_trucks_file)
        if os.path.exists(raw_trucks_path):
            with open(raw_trucks_path, 'r', encoding='utf-8') as f:
                results['raw_trucks'] = parse_csv_to_dict(f.read())
                print(f"Loaded {len(results['raw_trucks'])} trucks")
        
        raw_orders_file = f"rohdaten_auftraege_{latest_timestamp}.csv"
        raw_orders_path = os.path.join(results_dir, raw_orders_file)
        if os.path.exists(raw_orders_path):
            with open(raw_orders_path, 'r', encoding='utf-8') as f:
                results['raw_orders'] = parse_csv_to_dict(f.read())
                print(f"Loaded {len(results['raw_orders'])} orders")
        
        return results
        
    except Exception as e:
        print(f"DEBUG get_latest_results: Error reading result CSV files: {e}") # DEBUG
        import traceback
        traceback.print_exc() # Print full traceback
        return None

def parse_location_tuple(location_str):
    """Parse location string like '(27.5, 22.32)' into lat, lng"""
    print(f"DEBUG: parse_location_tuple received: '{location_str}'") # DEBUG
    try:
        # Remove parentheses and split by comma
        coords = location_str.strip('()').split(',')
        lat = float(coords[0].strip())
        lng = float(coords[1].strip())
        print(f"DEBUG: parse_location_tuple parsed to: ({lat}, {lng})") # DEBUG
        return lat, lng
    except Exception as e: # DEBUG: Catch specific exception and print it
        print(f"DEBUG: parse_location_tuple ERROR: {e} for input '{location_str}'") # DEBUG
        return 0.0, 0.0

def convert_backend_to_frontend_format(backend_results):
    """Convert backend CSV results to frontend data format"""
    if not backend_results:
        return None
    
    assignments = []
    trucks = []
    orders = []
    
    # Convert assigned orders to assignments
    if 'assigned_orders' in backend_results:
        for assigned in backend_results['assigned_orders']:
            assignments.append({
                'id': f"assignment-{assigned['lkw_id']}-{assigned['auftrag_id']}",
                'truckId': assigned['lkw_id'],
                'orderId': assigned['auftrag_id'],
                'distance': float(assigned['gesamtdistanz_fuer_auftrag_km']),
                'estimatedArrival': datetime.now().isoformat(),  # Simplified
                'status': 'assigned',
                'locked': False
            })
    
    # Get assigned truck IDs and order IDs for status determination
    assigned_truck_ids = set(a['truckId'] for a in assignments)
    assigned_order_ids = set(a['orderId'] for a in assignments)
    
    print(f"Assigned truck IDs: {assigned_truck_ids}")
    print(f"Assigned order IDs: {assigned_order_ids}")
    
    # Convert raw trucks
    if 'raw_trucks' in backend_results:
        truck_statuses = {}
        for truck in backend_results['raw_trucks']:
            lat, lng = parse_location_tuple(truck['location'])
            
            # Determine truck status based on assignments
            truck_status = 'idle'  # available
            if truck['truck_id'] in assigned_truck_ids:
                truck_status = 'loading'  # loaded/assigned
            
            truck_statuses[truck['truck_id']] = truck_status
            
            trucks.append({
                'id': truck['truck_id'],
                'name': f"Fahrzeug {truck['truck_id']}",
                'type': 'medium',  # Simplified
                'status': truck_status,
                'location': {
                    'lat': lat,
                    'lng': lng
                },
                'capacity': int(truck['capacity_kg']),
                'driver': f"Fahrer {truck['truck_id']}",
                'availableFrom': float(truck['available_from_h']),
                'availableTo': float(truck['available_until_h'])
            })
        
        print(f"Truck statuses: {truck_statuses}")
    
    # Convert raw orders
    if 'raw_orders' in backend_results:
        order_statuses = {}
        for order in backend_results['raw_orders']:
            pickup_lat, pickup_lng = parse_location_tuple(order['loading_site'])
            delivery_lat, delivery_lng = parse_location_tuple(order['unloading_site'])
            
            # Determine order status based on assignments
            order_status = 'pending'
            if order['order_id'] in assigned_order_ids:
                order_status = 'assigned'
            
            order_statuses[order['order_id']] = order_status
            
            # Map priority numbers to German labels
            priority_labels = {1: 'Hoch', 2: 'Mittel', 3: 'Niedrig'}
            priority_label = priority_labels.get(int(order['priority']), 'Niedrig')
            
            orders.append({
                'id': order['order_id'],
                'customer': f"Kunde {order['order_id']}",
                'priority': int(order['priority']),
                'priorityLabel': priority_label,
                'pickupLocation': {
                    'lat': pickup_lat,
                    'lng': pickup_lng,
                    'address': f"Abholort {order['order_id']}"
                },
                'deliveryLocation': {
                    'lat': delivery_lat,
                    'lng': delivery_lng,
                    'address': f"Lieferort {order['order_id']}"
                },
                'timeWindow': {
                    'start': datetime.now().isoformat(),  # Simplified
                    'end': datetime.now().isoformat()     # Simplified
                },
                'size': int(float(order['weight_kg']) / 1000),
                'status': order_status,
                'loadingDuration': float(order['loading_duration_h']),
                'unloadingDuration': float(order['unloading_duration_h']),
                'weight': int(order['weight_kg'])
            })
        
        print(f"Order statuses: {order_statuses}")
    
    result = {
        'trucks': trucks,
        'orders': orders,
        'assignments': assignments,
        'metrics': {
            'totalDistance': sum(float(a.get('distance', 0)) for a in assignments),
            'assignedOrders': len(assignments),
            'unassignedOrders': len(backend_results.get('unassigned_orders', [])),
            'fleetUtilization': (len(assignments) / len(trucks) * 100) if trucks else 0
        }
    }
    
    print(f"Final result summary:")
    print(f"  - Trucks: {len(result['trucks'])} (statuses: {[t['status'] for t in result['trucks']]})")
    print(f"  - Orders: {len(result['orders'])} (statuses: {[o['status'] for o in result['orders']]})")
    print(f"  - Assignments: {len(result['assignments'])}")
    
    return result

@app.route('/api/optimize', methods=['POST'])
def optimize():
    """Run optimization and return results"""
    try:
        # Get request data (optimization parameters from frontend)
        request_data = request.get_json() or {}
        
        print(f"Received optimization request: {request_data}")
        
        # Run the backend optimization script
        script_path = "../dispo/dispo.py"
        python_executable = sys.executable
        
        # Use absolute paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "..", "dispo", "dispo.py")
        script_path = os.path.abspath(script_path)
        
        print(f"Running script: {script_path}")
        print(f"Python executable: {python_executable}")
        
        # Run in the correct directory
        result = subprocess.run([
            python_executable, script_path
        ], 
        capture_output=True, 
        text=True, 
        cwd=os.path.dirname(script_path),
        encoding='cp1252',  # Windows encoding that handles German characters
        errors='replace'  # Handle encoding errors gracefully
        )
        
        print(f"Script return code: {result.returncode}")
        print(f"Script stdout: {result.stdout}")
        if result.stderr:
            print(f"Script stderr: {result.stderr}")
        
        if result.returncode == 0:
            print("Script completed successfully, parsing results...")
            
            # Parse the results
            backend_results = get_latest_results()
            
            if backend_results:
                print("Backend results found, converting to frontend format...")
                frontend_data = convert_backend_to_frontend_format(backend_results)
                
                if frontend_data:
                    print(f"Frontend data converted successfully:")
                    print(f"  - Trucks: {len(frontend_data.get('trucks', []))}")
                    print(f"  - Orders: {len(frontend_data.get('orders', []))}")
                    print(f"  - Assignments: {len(frontend_data.get('assignments', []))}")
                    
                    return jsonify({
                        'status': 'success',
                        'message': 'Optimierung erfolgreich abgeschlossen',
                        'data': frontend_data,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    print("Failed to convert backend results to frontend format")
                    return jsonify({
                        'status': 'error',
                        'message': 'Fehler bei der Datenkonvertierung'
                    }), 500
            else:
                print("No backend results found")
                return jsonify({
                    'status': 'error',
                    'message': 'Keine Ergebnisse gefunden'
                }), 500
        else:
            print("Script failed")
            return jsonify({
                'status': 'error',
                'message': f'Optimierung fehlgeschlagen: {result.stderr or result.stdout}'
            }), 500
            
    except Exception as e:
        print(f"API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Server Fehler: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Truck Dispatch Optimization API ist verfügbar',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/results/latest', methods=['GET'])
def latest_results():
    """Get the latest optimization results without running optimization"""
    try:
        backend_results = get_latest_results()
        
        if backend_results:
            frontend_data = convert_backend_to_frontend_format(backend_results)
            return jsonify({
                'status': 'success',
                'data': frontend_data,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Keine Ergebnisse verfügbar'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Fehler beim Laden der Ergebnisse: {str(e)}'
        }), 500

@app.route('/api/generate-data', methods=['POST'])
def generate_data():
    print("--- DEBUG: /api/generate-data endpoint hit ---")
    """Generate raw unassigned truck and order data without optimization"""
    try:
        # Run the backend script with a special flag to only generate data
        script_path = "../dispo/dispo.py"
        python_executable = sys.executable
        
        # Use absolute paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "..", "dispo", "dispo.py")
        script_path = os.path.abspath(script_path)
        
        print(f"Generating raw data without optimization...")
        
        # For now, we'll run the script and then only return the raw data
        result = subprocess.run([
            python_executable, script_path
        ], 
        capture_output=True, 
        text=True, 
        cwd=os.path.dirname(script_path),
        encoding='cp1252',
        errors='replace'
        )
        
        if result.returncode == 0:
            # Get the latest raw data but ignore optimization results
            backend_results = get_latest_results()
            
            if backend_results and 'raw_trucks' in backend_results and 'raw_orders' in backend_results:
                # Convert only raw data without assignments
                trucks = []
                orders = []
                
                # Convert raw trucks (all idle, no assignments)
                for truck in backend_results['raw_trucks']:
                    lat, lng = parse_location_tuple(truck['location'])
                    trucks.append({
                        'id': truck['truck_id'],
                        'name': f"Fahrzeug {truck['truck_id']}",
                        'type': 'medium',
                        'status': 'idle',  # All trucks start idle
                        'location': {
                            'lat': lat,
                            'lng': lng
                        },
                        'capacity': int(truck['capacity_kg']),
                        'driver': f"Fahrer {truck['truck_id']}",
                        'availableFrom': float(truck['available_from_h']),
                        'availableTo': float(truck['available_until_h'])
                    })
                
                # Convert raw orders (all pending, no assignments)
                for order in backend_results['raw_orders']:
                    pickup_lat, pickup_lng = parse_location_tuple(order['loading_site'])
                    delivery_lat, delivery_lng = parse_location_tuple(order['unloading_site'])
                    
                    priority_labels = {1: 'Hoch', 2: 'Mittel', 3: 'Niedrig'}
                    priority_label = priority_labels.get(int(order['priority']), 'Niedrig')
                    
                    orders.append({
                        'id': order['order_id'],
                        'customer': f"Kunde {order['order_id']}",
                        'priority': int(order['priority']),
                        'priorityLabel': priority_label,
                        'pickupLocation': {
                            'lat': pickup_lat,
                            'lng': pickup_lng,
                            'address': f"Abholort {order['order_id']}"
                        },
                        'deliveryLocation': {
                            'lat': delivery_lat,
                            'lng': delivery_lng,
                            'address': f"Lieferort {order['order_id']}"
                        },
                        'timeWindow': {
                            'start': datetime.now().isoformat(),
                            'end': datetime.now().isoformat()
                        },
                        'size': int(float(order['weight_kg']) / 1000),
                        'status': 'pending',  # All orders start pending
                        'loadingDuration': float(order['loading_duration_h']),
                        'unloadingDuration': float(order['unloading_duration_h']),
                        'weight': int(order['weight_kg'])
                    })
                
                raw_data = {
                    'trucks': trucks,
                    'orders': orders,
                    'assignments': [],  # No assignments initially
                    'metrics': {
                        'totalDistance': 0,
                        'assignedOrders': 0,
                        'unassignedOrders': len(orders),
                        'fleetUtilization': 0
                    }
                }
                
                print(f"Generated raw data:")
                print(f"  - Trucks: {len(trucks)} (all idle)")
                print(f"  - Orders: {len(orders)} (all pending)")
                print(f"  - Assignments: 0")
                
                return jsonify({
                    'status': 'success',
                    'message': 'Rohdaten erfolgreich generiert',
                    'data': raw_data,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Fehler beim Laden der Rohdaten'
                }), 500
        else:
            return jsonify({
                'status': 'error',
                'message': f'Datengenerierung fehlgeschlagen: {result.stderr or result.stdout}'
            }), 500
            
    except Exception as e:
        print(f"Generate Data API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Server Fehler: {str(e)}'
        }), 500

# Serve React App
@app.route('/')
def serve_react_app():
    """Serve the React application"""
    try:
        return send_from_directory(app.static_folder, 'index.html')
    except:
        return jsonify({'error': 'Frontend not built. Run: cd src/front && npm run build'}), 404

@app.route('/<path:path>')
def serve_react_static(path):
    """Serve React static files"""
    try:
        return send_from_directory(app.static_folder, path)
    except:
        # Fallback to index.html for client-side routing
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    print("Starting Truck Dispatch Optimization API Server...")
    
    # Use environment PORT for production deployment (Heroku, Railway, Render)
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'  # Required for cloud deployment
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"Frontend should connect to: http://localhost:{port}")
    print(f"Running in {'development' if debug else 'production'} mode")
    
    app.run(debug=debug, port=port, host=host) 