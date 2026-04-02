"""
Flask Application Module
Main Flask application initialization
"""
from flask import Flask
from config import config
import os

def create_app(config_name='development'):
    """
    Application factory function
    
    Args:
        config_name (str): Configuration name (development, production, testing)
    Returns:
        Flask: Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Enable CORS for API endpoints
    try:
        from flask_cors import CORS
        CORS(app, resources={r"/api/*": {"origins": "*"}})
    except ImportError:
        pass
    
    # Register blueprints and routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
