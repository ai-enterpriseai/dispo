#!/usr/bin/env python3

from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'ok',
        'message': 'Backend is running!',
        'python_version': os.sys.version
    })

@app.route('/api/test')
def test():
    return jsonify({
        'status': 'success',
        'message': 'API is working!',
        'endpoints': ['/api/status', '/api/test']
    })

if __name__ == '__main__':
    print("🚛 Starting Simple Test Server...")
    print("Visit: http://localhost:5000/api/status")
    app.run(debug=True, port=5000, host='0.0.0.0') 