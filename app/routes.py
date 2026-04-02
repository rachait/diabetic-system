"""
Flask Routes Module
Define all application routes and request handlers
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import sys
import numpy as np
import joblib
import pandas as pd
from config import Config

# Add models directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

main_bp = Blueprint('main', __name__)

# Global variables to store model and scaler
model = None
scaler = None
feature_names = None

def load_model_and_scaler():
    """Load the best model and scaler"""
    global model, scaler, feature_names
    
    try:
        if os.path.exists(Config.BEST_MODEL_PATH):
            model = joblib.load(Config.BEST_MODEL_PATH)
            print("Model loaded successfully")
        
        if os.path.exists(Config.SCALER_PATH):
            scaler = joblib.load(Config.SCALER_PATH)
            print("Scaler loaded successfully")
        
        feature_names = Config.FEATURE_NAMES
        return True
    except Exception as e:
        print(f"Error loading model or scaler: {str(e)}")
        return False

@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main_bp.route('/predict', methods=['GET', 'POST'])
def predict():
    """Prediction page"""
    if request.method == 'POST':
        try:
            prediction = None
            probability = None
            
            # Get input data
            input_data = {
                'Pregnancies': float(request.form.get('pregnancies', 0)),
                'Glucose': float(request.form.get('glucose', 0)),
                'BloodPressure': float(request.form.get('blood_pressure', 0)),
                'SkinThickness': float(request.form.get('skin_thickness', 0)),
                'Insulin': float(request.form.get('insulin', 0)),
                'BMI': float(request.form.get('bmi', 0)),
                'DiabetesPedigreeFunction': float(request.form.get('diabetes_pedigree', 0)),
                'Age': float(request.form.get('age', 0))
            }
            
            if model is not None and scaler is not None:
                # Prepare features in correct order
                features = np.array([
                    input_data['Pregnancies'],
                    input_data['Glucose'],
                    input_data['BloodPressure'],
                    input_data['SkinThickness'],
                    input_data['Insulin'],
                    input_data['BMI'],
                    input_data['DiabetesPedigreeFunction'],
                    input_data['Age']
                ]).reshape(1, -1)
                
                # Scale features
                features_scaled = scaler.transform(features)
                
                # Make prediction
                prediction = int(model.predict(features_scaled)[0])
                
                # Get prediction probability
                try:
                    prob = model.predict_proba(features_scaled)
                    probability = float(prob[0][prediction]) * 100
                except:
                    probability = None
                
                result = {
                    'status': 'success',
                    'prediction': 'Diabetic' if prediction == 1 else 'Non-Diabetic',
                    'confidence': probability,
                    'input_data': input_data
                }
            else:
                result = {
                    'status': 'error',
                    'message': 'Model not available. Please train the model first.'
                }
            
            return render_template('results.html', result=result)
        
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return redirect(url_for('main.predict'))
        except Exception as e:
            flash(f'Prediction error: {str(e)}', 'error')
            return redirect(url_for('main.predict'))
    
    return render_template('predict.html')

@main_bp.route('/api/predict', methods=['POST'])
def api_predict():
    """API endpoint for predictions"""
    try:
        data = request.get_json()
        
        if model is None or scaler is None:
            return jsonify({
                'status': 'error',
                'message': 'Model not available'
            }), 500
        
        # Prepare features
        features = np.array([
            data.get('pregnancies', 0),
            data.get('glucose', 0),
            data.get('blood_pressure', 0),
            data.get('skin_thickness', 0),
            data.get('insulin', 0),
            data.get('bmi', 0),
            data.get('diabetes_pedigree', 0),
            data.get('age', 0)
        ]).reshape(1, -1)
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Make prediction
        prediction = int(model.predict(features_scaled)[0])
        
        # Get probability
        try:
            prob = model.predict_proba(features_scaled)
            probability = float(prob[0][prediction])
        except:
            probability = None
        
        return jsonify({
            'status': 'success',
            'prediction': 'Diabetic' if prediction == 1 else 'Non-Diabetic',
            'confidence': probability,
            'prediction_value': prediction
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@main_bp.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'scaler_loaded': scaler is not None
    })

# Load model on startup
load_model_and_scaler()
