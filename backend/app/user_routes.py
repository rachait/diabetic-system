"""
User-facing endpoints for doctors, appointments, and orders
"""
from flask import Blueprint, request, jsonify, session
from database import get_db_connection

user_bp = Blueprint('user', __name__, url_prefix='/user')

def get_user_id():
    return session.get('user_id')

# List doctors (for users)
@user_bp.route('/doctors', methods=['GET'])
def list_doctors():
    conn = get_db_connection()
    doctors = conn.execute('SELECT * FROM doctors WHERE status != "inactive"').fetchall()
    conn.close()
    return jsonify({'status': 'success', 'doctors': [dict(row) for row in doctors]})

# List user's appointments
@user_bp.route('/appointments', methods=['GET'])
def list_appointments():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    conn = get_db_connection()
    appts = conn.execute('''
        SELECT a.*, d.name AS doctor_name
        FROM appointments a
        LEFT JOIN doctors d ON a.doctor_id = d.id
        WHERE a.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return jsonify({'status': 'success', 'appointments': [dict(row) for row in appts]})

# Book appointment
@user_bp.route('/appointments', methods=['POST'])
def book_appointment():
    user_id = get_user_id()
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
    data = request.get_json() or {}
    conn = get_db_connection()
    conn.execute('''INSERT INTO appointments (user_id, doctor_id, appointment_date, time_slot, appointment_type, status) VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, data.get('doctor_id'), data.get('appointment_date'), data.get('time_slot'), data.get('appointment_type', 'in-person'), 'confirmed'))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Get available slots for a doctor and date
@user_bp.route('/appointments/slots', methods=['GET'])
def get_appointment_slots():
    doctor_id = request.args.get('doctor_id', type=int)
    date = request.args.get('date', type=str)
    if not doctor_id or not date:
        return jsonify({'status': 'error', 'message': 'Missing doctor_id or date'}), 400
    # Example: 9am to 5pm, every hour
    all_slots = [f"{h:02d}:00" for h in range(9, 17)]
    conn = get_db_connection()
    booked = conn.execute('SELECT time_slot FROM appointments WHERE doctor_id = ? AND appointment_date = ?', (doctor_id, date)).fetchall()
    booked_slots = {row['time_slot'] for row in booked}
    slots = []
    for slot in all_slots:
        slots.append({
            'time_slot': slot,
            'status': 'booked' if slot in booked_slots else 'free'
        })
    conn.close()
    return jsonify({'status': 'success', 'slots': slots})
