from flask import Blueprint
from app.user_routes import list_doctors, list_appointments, book_appointment, get_appointment_slots

user_api_bp = Blueprint('user_api', __name__, url_prefix='/api/user')

# Route aliases for /api/user/* endpoints
user_api_bp.add_url_rule('/doctors', view_func=list_doctors, methods=['GET'])
user_api_bp.add_url_rule('/appointments', view_func=list_appointments, methods=['GET'])
user_api_bp.add_url_rule('/appointments', view_func=book_appointment, methods=['POST'])
user_api_bp.add_url_rule('/appointments/slots', view_func=get_appointment_slots, methods=['GET'])
