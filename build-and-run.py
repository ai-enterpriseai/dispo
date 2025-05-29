#!/usr/bin/env python3
"""
Single Service Deployment Script
Builds the React frontend and runs Flask to serve both frontend and API
"""

import subprocess
import sys
import os

def build_frontend():
    """Build the React frontend"""
    print("🔨 Building React frontend...")
    
    frontend_dir = "src/front"
    
    if not os.path.exists(frontend_dir):
        print("❌ Frontend directory not found!")
        return False
    
    try:
        # Install dependencies
        subprocess.run(["npm", "install", "--legacy-peer-deps"], 
                      cwd=frontend_dir, check=True)
        
        # Build the app
        subprocess.run(["npm", "run", "build"], 
                      cwd=frontend_dir, check=True)
        
        print("✅ Frontend built successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend build failed: {e}")
        return False

def run_server():
    """Run the Flask server"""
    print("🚀 Starting Flask server (frontend + API)...")
    subprocess.run([sys.executable, "src/api/server.py"])

if __name__ == "__main__":
    print("🚛 Single Service Deployment")
    print("=" * 40)
    
    # Build frontend first
    if build_frontend():
        # Run the server
        run_server()
    else:
        print("❌ Deployment failed - could not build frontend")
        sys.exit(1) 