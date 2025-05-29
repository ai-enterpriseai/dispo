#!/usr/bin/env python3
"""
Local Development Startup Script
Starts both frontend (React) and backend (Flask API) services
"""

import subprocess
import sys
import time
import webbrowser
from threading import Thread

def start_frontend():
    """Start the React frontend development server"""
    print("🚀 Starting Frontend (React + Vite)...")
    try:
        subprocess.run([
            "npm", "run", "dev"
        ], cwd="src/front", shell=True)
    except Exception as e:
        print(f"❌ Frontend failed to start: {e}")

def start_api_server():
    """Start the Flask API server"""
    print("🚀 Starting API Server (Flask)...")
    try:
        subprocess.run([
            sys.executable, "src/api/server.py"
        ], shell=True)
    except Exception as e:
        print(f"❌ API Server failed to start: {e}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Node.js/npm
    try:
        subprocess.run(["npm", "--version"], capture_output=True, check=True)
        print("✅ Node.js/npm found")
    except:
        print("❌ Node.js/npm not found. Please install Node.js from https://nodejs.org/")
        return False
    
    # Check Python packages
    try:
        import flask
        import flask_cors
        import pulp
        print("✅ Python packages found")
    except ImportError as e:
        print(f"❌ Missing Python package: {e}")
        print("   Run: pip install flask flask-cors pulp")
        return False
    
    return True

def main():
    print("=" * 60)
    print("🚛 TRUCK DISPATCH OPTIMIZATION SYSTEM")
    print("=" * 60)
    
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        return
    
    print("\n🎯 Starting all services...")
    
    # Start API server in background
    api_thread = Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Give API server time to start
    time.sleep(3)
    
    print("\n📊 Services should be running on:")
    print("   Frontend: http://localhost:5173")
    print("   API:      http://localhost:5000")
    print("   API Status: http://localhost:5000/api/status")
    
    # Open browser
    print("\n🌐 Opening browser...")
    time.sleep(2)
    webbrowser.open("http://localhost:5173")
    
    # Start frontend (this blocks)
    print("\n🎨 Starting frontend (this will block)...")
    print("   Press Ctrl+C to stop all services")
    start_frontend()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        print("   Goodbye!") 