"""
Flask Routes Module (Diabetes Backend)
Define all application routes and request handlers
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import os
import sys
import numpy as np
import joblib
import time
from config import Config
from .utils import validate_prediction_input

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

main_bp = Blueprint('main', __name__)

# Global variables to store model and scaler
model = None
scaler = None
feature_names = None
predict_rate_bucket = {}


def _confidence_band(probability):
    """Human-friendly confidence band for UI messaging."""
    if probability is None:
        return 'unknown'
    if probability >= 0.85:
        return 'high'
    if probability >= 0.65:
        return 'moderate'
    return 'low'


def _check_rate_limit(client_id, limit=20, window_seconds=60):
    """Simple in-memory sliding window rate limiter for prediction API."""
    now = time.time()
    timestamps = predict_rate_bucket.get(client_id, [])
    timestamps = [ts for ts in timestamps if now - ts <= window_seconds]
    if len(timestamps) >= limit:
        predict_rate_bucket[client_id] = timestamps
        return False
    timestamps.append(now)
    predict_rate_bucket[client_id] = timestamps
    return True


def _extract_explanations(input_payload, scaler_obj):
    """Generate lightweight feature impact hints from standardized distance."""
    if scaler_obj is None or not hasattr(scaler_obj, 'mean_') or not hasattr(scaler_obj, 'scale_'):
        return []

    keys = [
        'pregnancies', 'glucose', 'blood_pressure', 'skin_thickness',
        'insulin', 'bmi', 'diabetes_pedigree', 'age'
    ]
    labels = {
        'pregnancies': 'Pregnancies',
        'glucose': 'Glucose',
        'blood_pressure': 'Blood Pressure',
        'skin_thickness': 'Skin Thickness',
        'insulin': 'Insulin',
        'bmi': 'BMI',
        'diabetes_pedigree': 'Diabetes Pedigree',
        'age': 'Age'
    }

    explanation_rows = []
    for idx, key in enumerate(keys):
        try:
            raw_value = float(input_payload.get(key, 0))
            std = float(scaler_obj.scale_[idx]) if float(scaler_obj.scale_[idx]) != 0 else 1.0
            z_score = (raw_value - float(scaler_obj.mean_[idx])) / std
            explanation_rows.append({
                'feature': key,
                'label': labels[key],
                'value': raw_value,
                'z_score': round(z_score, 2),
                'direction': 'elevated' if z_score >= 0 else 'below average',
                'magnitude': abs(z_score)
            })
        except Exception:
            continue

    explanation_rows.sort(key=lambda item: item['magnitude'], reverse=True)
    return explanation_rows[:3]


def _build_action_plan(risk_level):
    """Return a simple 7-day plan scaffold tied to risk level."""
    low_plan = [
        'Day 1: 30-minute brisk walk and hydrate well.',
        'Day 2: Build a plate with half vegetables at lunch and dinner.',
        'Day 3: Sleep target 7-8 hours and avoid late sugary snacks.',
        'Day 4: Add one strength session (20-30 minutes).',
        'Day 5: Replace one refined-carb meal with whole grains/legumes.',
        'Day 6: Post-meal 10-minute walk after major meals.',
        'Day 7: Review weekly habits and plan next week.'
    ]
    medium_plan = [
        'Day 1: Remove sugary drinks and track meals.',
        'Day 2: 35-minute walk plus high-fiber breakfast.',
        'Day 3: Check fasting glucose if available and log it.',
        'Day 4: Add lean protein to each major meal.',
        'Day 5: 40-minute activity split into two sessions if needed.',
        'Day 6: Meal-prep low-glycemic options for 3 days.',
        'Day 7: Reassess weight/waist and set next 7-day target.'
    ]
    high_plan = [
        'Day 1: Schedule clinician follow-up for confirmatory testing.',
        'Day 2: Stop sugary beverages and reduce refined carbs sharply.',
        'Day 3: 20-30 minutes low-impact activity after medical clearance.',
        'Day 4: Focus meals on non-starchy vegetables and lean protein.',
        'Day 5: Monitor glucose as advised by healthcare provider.',
        'Day 6: Prepare medication and meal adherence checklist.',
        'Day 7: Review symptoms and share logs with clinician.'
    ]
    if risk_level == 'high':
        return high_plan
    if risk_level == 'medium':
        return medium_plan
    return low_plan


def _input_warnings(input_payload):
    """Return non-blocking quality and safety warnings for unusual inputs."""
    warnings = []
    glucose = float(input_payload.get('glucose', 0))
    bmi = float(input_payload.get('bmi', 0))
    blood_pressure = float(input_payload.get('blood_pressure', 0))
    insulin = float(input_payload.get('insulin', 0))

    if glucose >= 200:
        warnings.append('Glucose is very high; seek prompt clinical evaluation.')
    elif glucose >= 140:
        warnings.append('Glucose appears elevated; consider follow-up testing.')

    if bmi >= 35:
        warnings.append('BMI is in a high-risk range; structured weight management may help.')

    if blood_pressure >= 100:
        warnings.append('Diastolic blood pressure appears elevated; monitor closely.')

    if insulin >= 300:
        warnings.append('Insulin value is unusually high; verify measurement and discuss with clinician.')

    if bmi < 16 or blood_pressure < 40:
        warnings.append('Some inputs look unusual; please verify entered values for accuracy.')

    return warnings


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
    """Home page - show dashboard"""
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
                except Exception:
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
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr) or 'unknown-client'
        if not _check_rate_limit(client_ip):
            return jsonify({
                'status': 'error',
                'message': 'Too many prediction requests. Please wait a moment and retry.'
            }), 429

        data = request.get_json() or {}

        valid, validation_error = validate_prediction_input(data)
        if not valid:
            return jsonify({
                'status': 'error',
                'message': validation_error
            }), 400

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
        except Exception:
            probability = None

        risk_level = 'high' if prediction == 1 and probability is not None and probability >= 0.8 else 'medium' if prediction == 1 else 'low'
        confidence_band = _confidence_band(probability)
        explanation_factors = _extract_explanations(data, scaler)
        warnings = _input_warnings(data)
        emergency_notice = 'Seek urgent medical evaluation for very high glucose readings or concerning symptoms.' if float(data.get('glucose', 0)) >= 250 else None
        suggestions = {
            'high': [
                'Consult a doctor for confirmatory blood tests.',
                'Reduce sugary drinks and refined carbs immediately.',
                'Add daily low-impact physical activity.'
            ],
            'medium': [
                'Follow portion control and high-fiber meals.',
                'Track fasting glucose and weight weekly.',
                'Target at least 150 minutes of exercise per week.'
            ],
            'low': [
                'Maintain balanced meals and hydration.',
                'Keep a consistent exercise routine.',
                'Repeat screening as advised by your clinician.'
            ]
        }

        return jsonify({
            'status': 'success',
            'prediction': 'Diabetic' if prediction == 1 else 'Non-Diabetic',
            'confidence': probability,
            'confidence_band': confidence_band,
            'prediction_value': prediction,
            'risk_level': risk_level,
            'suggestions': suggestions[risk_level],
            'action_plan_7d': _build_action_plan(risk_level),
            'explanation_factors': explanation_factors,
            'warnings': warnings,
            'emergency_notice': emergency_notice,
            'model_version': getattr(Config, 'MODEL_VERSION', 'v1')
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

# Simulated IoT device data generator (for demo/testing)
@main_bp.route('/api/iot/simulate', methods=['GET'])
def simulate_iot_data():
    """Simulate IoT device sending random sensor data and get prediction"""
    import random
    # Generate random but plausible values for each feature
    simulated_data = {
        'device_id': f'device_{random.randint(1000,9999)}',
        'pregnancies': random.randint(0, 10),
        'glucose': random.randint(70, 200),
        'blood_pressure': random.randint(60, 120),
        'skin_thickness': random.randint(10, 50),
        'insulin': random.randint(15, 276),
        'bmi': round(random.uniform(18.0, 45.0), 1),
        'diabetes_pedigree': round(random.uniform(0.1, 2.5), 2),
        'age': random.randint(18, 80)
    }
    # Use the existing /api/iot/data logic by making an internal request
    from flask import current_app
    with current_app.test_request_context('/api/iot/data', method='POST', json=simulated_data):
        resp = iot_data()
        # If the response is a tuple (response, status), extract the response
        if isinstance(resp, tuple):
            return resp[0]
        return resp


@main_bp.route('/api/iot/data', methods=['POST'])
def iot_data():
    """Endpoint for IoT devices to POST sensor readings and get prediction"""
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id')

        # Map incoming fields to expected model inputs (use defaults if missing)
        features = np.array([
            float(data.get('pregnancies', 0)),
            float(data.get('glucose', 0)),
            float(data.get('blood_pressure', 0)),
            float(data.get('skin_thickness', 0)),
            float(data.get('insulin', 0)),
            float(data.get('bmi', 0)),
            float(data.get('diabetes_pedigree', 0)),
            float(data.get('age', 0))
        ]).reshape(1, -1)

        if model is None or scaler is None:
            return jsonify({'status': 'error', 'message': 'Model not available'}), 500

        features_scaled = scaler.transform(features)
        prediction_value = int(model.predict(features_scaled)[0])
        probability = None
        try:
            prob = model.predict_proba(features_scaled)
            probability = float(prob[0][prediction_value])
        except Exception:
            probability = None

        return jsonify({
            'status': 'success',
            'device_id': device_id,
            'prediction': 'Diabetic' if prediction_value == 1 else 'Non-Diabetic',
            'prediction_value': prediction_value,
            'confidence': probability
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
