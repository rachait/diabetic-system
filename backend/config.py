"""
Configuration settings for the Diabetes Prediction System (Backend)
"""
import os

class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    MODEL_VERSION = os.environ.get('MODEL_VERSION', 'v1.0.0')

    # Paths (relative to project root)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    ROOT_DIR = os.path.dirname(BASE_DIR)

    MODEL_DIR = os.path.join(ROOT_DIR, 'models')
    DATA_DIR = os.path.join(ROOT_DIR, 'data')

    # Model filenames
    BEST_MODEL_PATH = os.path.join(MODEL_DIR, 'best_model.pkl')
    SCALER_PATH = os.path.join(MODEL_DIR, 'scaler.pkl')

    # Feature names
    FEATURE_NAMES = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
                     'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age']

    # Flask settings
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True

# Export config
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
