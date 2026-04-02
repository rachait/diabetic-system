"""
Flask Application Module (Diabetes Backend)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask
from config import config

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, 'app', 'templates')
STATIC_DIR = os.path.join(PROJECT_ROOT, 'app', 'static')


def create_app(config_name='development'):
    """Application factory function"""
    app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR, static_url_path='/static')

    # Load configuration
    app.config.from_object(config[config_name])
    
    # Enable sessions
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 24 * 60 * 60  # 24 hours
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = bool(os.environ.get('SESSION_COOKIE_SECURE', '').lower() == 'true')

    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize database
    from database import init_db, seed_products
    init_db()
    seed_products()

    # Enable CORS for API endpoints and allow session cookies from frontend.
    try:
        from flask_cors import CORS
        allowed_origins = os.environ.get(
            'FRONTEND_ORIGINS',
            'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000'
        ).split(',')
        CORS(
            app,
            resources={r"/api/*": {"origins": [origin.strip() for origin in allowed_origins]}},
            supports_credentials=True
        )
    except ImportError:
        pass

    # Register blueprints
    from app.routes import main_bp
    from app.auth_routes import auth_bp
    from app.store_routes import store_bp
    from app.wellness_routes import wellness_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(wellness_bp)

    @app.after_request
    def set_security_headers(response):
        """Attach baseline security headers."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    return app
