"""
Utility functions for the Flask application
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
    """
    Validate prediction input data
    
    Args:
        data (dict): Input data dictionary
        
    Returns:
        tuple: (is_valid, error_message)
    """
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
        except ValueError:
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
    
    return True, None

def format_prediction_result(prediction, probability=None):
    """
    Format prediction result for display
    
    Args:
        prediction (int): 0 or 1
        probability (float): Prediction probability
        
    Returns:
        dict: Formatted result
    """
    result = {
        'prediction_text': 'Diabetic' if prediction == 1 else 'Non-Diabetic',
        'prediction_value': prediction,
        'risk_level': 'High Risk' if prediction == 1 else 'Low Risk'
    }
    
    if probability is not None:
        result['confidence'] = f"{probability * 100:.2f}%"
    
    return result
