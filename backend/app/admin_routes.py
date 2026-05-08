"""
Admin Doctor Management Routes
"""
from flask import Blueprint, request, jsonify, session
from database import get_db_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def is_admin():
    user_id = session.get('user_id')
    is_admin_flag = session.get('is_admin')
    if user_id and is_admin_flag:
        return True
    # Fallback: check the database directly
    if user_id:
        conn = get_db_connection()
        row = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        if row and int(row['is_admin'] or 0) == 1:
            session['is_admin'] = True
            return True
    return False

# Admin dashboard summary
@admin_bp.route('/dashboard', methods=['GET'])
def dashboard():
    if not is_admin():
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    conn = get_db_connection()
    total_doctors = conn.execute('SELECT COUNT(*) as c FROM doctors').fetchone()['c']
    available_today = conn.execute("SELECT COUNT(*) as c FROM doctors WHERE status = 'available'").fetchone()['c']
    from datetime import date
    today = date.today().isoformat()
    appointments_today = conn.execute('SELECT COUNT(*) as c FROM appointments WHERE appointment_date = ?', (today,)).fetchone()['c']
    conn.close()
    return jsonify({'status': 'success', 'total_doctors': total_doctors, 'available_today': available_today, 'appointments_today': appointments_today, 'average_rating': 0})

# List all doctors
@admin_bp.route('/doctors', methods=['GET'])
def list_doctors():
    if not is_admin():
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    from datetime import date
    today = date.today().isoformat()
    conn = get_db_connection()
    doctors = conn.execute('SELECT * FROM doctors').fetchall()
    total_doctors    = len(doctors)
    available_today  = sum(1 for d in doctors if d['status'] == 'available')
    appointments_today = conn.execute(
        'SELECT COUNT(*) as c FROM appointments WHERE appointment_date = ?', (today,)
    ).fetchone()['c']
    avg_rating_row = conn.execute(
        'SELECT AVG(average_rating) as r FROM doctors WHERE average_rating IS NOT NULL AND average_rating > 0'
    ).fetchone()
    avg_rating = round(avg_rating_row['r'] or 0, 1)
    conn.close()
    return jsonify({
        'status': 'success',
        'doctors': [dict(row) for row in doctors],
        'metrics': {
            'total_doctors': total_doctors,
            'available_today': available_today,
            'appointments_today': appointments_today,
            'average_rating': avg_rating,
        }
    })

# Add a doctor
@admin_bp.route('/doctors', methods=['POST'])
def add_doctor():
    if not is_admin():
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    data = request.get_json() or {}
    conn = get_db_connection()
    conn.execute('''INSERT INTO doctors (name, specialization, available_days, consultation_fee, status, avatar_url, slot_count) VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (data.get('name'), data.get('specialization'), data.get('available_days'), data.get('consultation_fee'), data.get('status', 'available'), data.get('avatar_url'), data.get('slot_count', 0)))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Edit a doctor
@admin_bp.route('/doctors/<int:doctor_id>', methods=['PUT'])
def edit_doctor(doctor_id):
    if not is_admin():
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    data = request.get_json() or {}
    conn = get_db_connection()
    conn.execute('''UPDATE doctors SET name=?, specialization=?, available_days=?, consultation_fee=?, status=?, avatar_url=?, slot_count=?, updated_at=CURRENT_TIMESTAMP WHERE id=?''',
        (data.get('name'), data.get('specialization'), data.get('available_days'), data.get('consultation_fee'), data.get('status'), data.get('avatar_url'), data.get('slot_count'), doctor_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Delete a doctor
@admin_bp.route('/doctors/<int:doctor_id>', methods=['DELETE'])
def delete_doctor(doctor_id):
    if not is_admin():
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    conn = get_db_connection()
    conn.execute('DELETE FROM doctors WHERE id=?', (doctor_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# List all appointments (admin - all users, optional date filter)
@admin_bp.route('/appointments', methods=['GET'])
def list_appointments():
    if not is_admin():
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    date_filter = request.args.get('date')
    conn = get_db_connection()
    if date_filter:
        appts = conn.execute('''
            SELECT a.*, d.name AS doctor_name, u.username, u.full_name AS patient_name
            FROM appointments a
            LEFT JOIN doctors d ON a.doctor_id = d.id
            LEFT JOIN users u ON a.user_id = u.id
            WHERE a.appointment_date = ?
        ''', (date_filter,)).fetchall()
    else:
        appts = conn.execute('''
            SELECT a.*, d.name AS doctor_name, u.username, u.full_name AS patient_name
            FROM appointments a
            LEFT JOIN doctors d ON a.doctor_id = d.id
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.appointment_date DESC
        ''').fetchall()
    appts_list = [dict(row) for row in appts]
    confirmed  = sum(1 for a in appts_list if a.get('status') == 'confirmed')
    pending    = sum(1 for a in appts_list if a.get('status') == 'pending')
    cancelled  = sum(1 for a in appts_list if a.get('status') == 'cancelled')
    conn.close()
    return jsonify({
        'status': 'success',
        'appointments': appts_list,
        'summary': {'confirmed': confirmed, 'pending': pending, 'cancelled': cancelled}
    })

# Create appointment (admin)
@admin_bp.route('/appointments', methods=['POST'])
def create_appointment():
    if not is_admin():
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    data = request.get_json() or {}
    user_id = data.get('user_id') or session.get('user_id')
    conn = get_db_connection()
    conn.execute('''INSERT INTO appointments (user_id, doctor_id, appointment_date, time_slot, appointment_type, status) VALUES (?, ?, ?, ?, ?, ?)''',
        (user_id, data.get('doctor_id'), data.get('appointment_date'), data.get('time_slot'), data.get('appointment_type', 'in-person'), 'confirmed'))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Cancel appointment (admin)
@admin_bp.route('/appointments/<int:appointment_id>/cancel', methods=['PATCH'])
def cancel_appointment(appointment_id):
    if not is_admin():
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    conn = get_db_connection()
    conn.execute("UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

# Get available slots for a doctor and date (admin)
@admin_bp.route('/appointments/slots', methods=['GET'])
def get_slots():
    if not is_admin():
        return jsonify({'status': 'error', 'message': 'Admin access required'}), 403
    doctor_id = request.args.get('doctor_id', type=int)
    date = request.args.get('date', type=str)
    if not doctor_id or not date:
        return jsonify({'status': 'error', 'message': 'Missing doctor_id or date'}), 400
    all_slots = [f"{h:02d}:00" for h in range(9, 17)]
    conn = get_db_connection()
    booked = conn.execute('SELECT time_slot FROM appointments WHERE doctor_id = ? AND appointment_date = ?', (doctor_id, date)).fetchall()
    booked_slots = {row['time_slot'] for row in booked}
    slots = [{'time_slot': s, 'status': 'booked' if s in booked_slots else 'free'} for s in all_slots]
    conn.close()
    return jsonify({'status': 'success', 'slots': slots})
