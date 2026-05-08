"""
Utility functions for the Diabetes Flask application
"""
import os
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'csv', 'xlsx'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_prediction_input(data):
    """Validate prediction input data"""

    # Require gender before pregnancies
    if 'gender' not in data or not str(data['gender']).strip():
        return False, "Missing or invalid gender. Please select gender before entering pregnancies."
    if str(data['gender']).strip().lower() not in {'male', 'female', 'other'}:
        return False, "gender must be Male, Female, or Other"

    required_fields = [
        'pregnancies', 'glucose', 'blood_pressure', 'skin_thickness',
        'insulin', 'bmi', 'diabetes_pedigree', 'age'
    ]

    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"

        try:
            value = float(data[field])
            if value < 0:
                return False, f"{field} cannot be negative"
        except (ValueError, TypeError):
            return False, f"Invalid value for {field}"

    # Range validations
    ranges = {
        'pregnancies': (0, 20),
        'glucose': (0, 300),
        'blood_pressure': (0, 200),
        'skin_thickness': (0, 100),
        'insulin': (0, 900),
        'bmi': (0, 100),
        'diabetes_pedigree': (0, 5),
        'age': (0, 120)
    }

    for field, (min_val, max_val) in ranges.items():
        value = float(data[field])
        if not (min_val <= value <= max_val):
            return False, f"{field} out of valid range ({min_val}-{max_val})"

    gender = data.get('gender')
    if gender is not None and str(gender).strip():
        if str(gender).strip().lower() not in {'male', 'female', 'other'}:
            return False, "gender must be Male, Female, or Other"

    return True, None


def format_prediction_result(prediction, probability=None):
    """Format prediction result for display"""
    result = {
        'prediction_text': 'Diabetic' if prediction == 1 else 'Non-Diabetic',
        'prediction_value': prediction,
        'risk_level': 'High Risk' if prediction == 1 else 'Low Risk'
    }

    if probability is not None:
        result['confidence'] = f"{probability * 100:.2f}%"

    return result
