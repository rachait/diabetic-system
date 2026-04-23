"""Diabetes Prediction System - Backend Entry Point"""

import os
from app import create_app

# Create Flask app
app = create_app('development')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    from flask import jsonify
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    from flask import jsonify
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# Root route
@app.route('/')
def index():
    from flask import jsonify
    return jsonify({'status': 'success', 'message': 'Diabetes Prediction Backend API', 'version': '1.0'}), 200

if __name__ == '__main__':
    # Ensure upload folder exists
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        os.makedirs(upload_folder, exist_ok=True)

    print("\n" + "="*70)
    print("Diabetes Prediction System - Backend Server")
    print("="*70)
    print("\nServer starting at: http://localhost:5000")
    print("Home: http://localhost:5000/")
    print("Predict: http://localhost:5000/predict")
    print("API: http://localhost:5000/api/predict")
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
