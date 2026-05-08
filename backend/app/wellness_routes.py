"""
Risk Assessment & Nutritionist Booking Routes
"""
from flask import Blueprint, request, jsonify, session
from database import DB_PATH, get_db_connection
import numpy as np
import os
from . import routes as diabetes_routes

wellness_bp = Blueprint('wellness', __name__, url_prefix='/api/wellness')


def _risk_band(prediction_value, confidence):
    """Map model output to user-friendly risk band."""
    if confidence is not None and confidence >= 0.75:
        return 'high'
    if confidence is not None and confidence >= 0.45:
        return 'medium'
    return 'medium' if prediction_value == 1 else 'low'


def _clinical_risk_floor(input_payload):
    """Rule-based minimum risk band for strong diabetic risk signals."""
    glucose = float(input_payload.get('glucose', 0))
    bmi = float(input_payload.get('bmi', 0))
    age = float(input_payload.get('age', 0))
    dpf = float(input_payload.get('diabetes_pedigree', 0))
    insulin = float(input_payload.get('insulin', 0))

    if glucose >= 200 or (glucose >= 180 and bmi >= 30) or (glucose >= 160 and insulin >= 250):
        return 'high'
    if glucose >= 140 or (bmi >= 30 and age >= 45) or (dpf >= 1.0 and age >= 35):
        return 'medium'
    return 'low'


def _diabetes_probability(model_obj, features_scaled):
    """Return probability of diabetic class (class label 1) if available."""
    if not hasattr(model_obj, 'predict_proba'):
        return None

    prob = model_obj.predict_proba(features_scaled)
    classes = getattr(model_obj, 'classes_', None)
    if classes is None:
        return float(prob[0][-1])

    for idx, cls in enumerate(classes):
        if int(cls) == 1:
            return float(prob[0][idx])
    return float(prob[0][-1])


def _normalize_chat_history(messages):
    """Keep a compact, JSON-safe subset of recent chat messages."""
    cleaned = []
    if not isinstance(messages, list):
        return cleaned

    for item in messages[-8:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get('role') or '').strip().lower()
        content = str(item.get('content') or '').strip()
        if role in {'user', 'assistant'} and content:
            cleaned.append({'role': role, 'content': content[:500]})
    return cleaned


def _latest_user_message(messages):
    """Return the latest user message from a chat transcript."""
    for item in reversed(messages or []):
        if isinstance(item, dict) and str(item.get('role') or '').lower() == 'user':
            return str(item.get('content') or '').strip()
    return ''


def _compose_chatbot_reply(question, risk_level='', glucose=None, bmi=None, chat_history=None):
    """Generate a conversational wellness reply."""
    question_text = (question or '').strip()
    lowered = question_text.lower()
    recent_user_question = _latest_user_message(chat_history) or question_text

    answer = (
        "I can help with your result, food, exercise, symptoms, prevention, and next steps. "
        "Ask me a specific question and I’ll keep it short and practical."
    )

    if any(term in lowered for term in ['result', 'prediction', 'confidence', 'risk']):
        if risk_level == 'high':
            answer = (
                "Based on your result, this looks like a high-risk pattern. "
                "The safest next step is to arrange confirmatory testing and follow clinician guidance. "
                "If you want, I can turn this into a simple 3-step action plan."
            )
        elif risk_level == 'medium':
            answer = (
                "Your result suggests moderate risk. That usually means the best move is small consistent changes: "
                "cut sugary drinks, increase fiber and protein, and keep active most days. "
                "I can also explain which inputs pushed the score up."
            )
        elif risk_level == 'low':
            answer = (
                "Your result looks lower risk right now. Keep the habits that protect you: balanced meals, "
                "regular exercise, good sleep, and periodic screening."
            )

    elif any(term in lowered for term in ['diet', 'food', 'meal', 'eat', 'nutrition']):
        answer = (
            "For food, focus on vegetables, legumes, lean protein, nuts, and whole grains. "
            "Limit sugary drinks, refined snacks, and oversized portions. If you want, I can build a sample day of meals."
        )
    elif any(term in lowered for term in ['exercise', 'excerise', 'excercise', 'workout', 'activity', 'walk']):
        answer = (
            "Exercise means regular movement that helps your body use glucose better. "
            "A simple target is 30 minutes of brisk activity on most days plus 2 strength sessions each week. "
            "Even a 10-minute walk after meals helps."
        )
    elif any(term in lowered for term in ['hello', 'hi', 'hey']):
        answer = (
            "Hi. I’m here to help with diabetes questions, your result, food choices, exercise, and prevention. "
            "What would you like to focus on first?"
        )
    elif 'symptom' in lowered or 'sign' in lowered:
        answer = (
            "Common warning signs can include increased thirst, frequent urination, fatigue, blurred vision, "
            "and unexpected weight changes. If you have severe symptoms, seek medical care promptly."
        )
    else:
        answer = (
            f"I read your last question as: {recent_user_question}. "
            "I can explain the result, translate medical terms, suggest food or exercise plans, or help you ask a clinician better questions."
        )

    insights = []
    if glucose is not None:
        try:
            glucose_val = float(glucose)
            if glucose_val >= 180:
                insights.append('Glucose is quite high; follow up with a clinician soon.')
            elif glucose_val >= 140:
                insights.append('Glucose is elevated; repeat testing and watch diet choices.')
        except Exception:
            pass

    if bmi is not None:
        try:
            bmi_val = float(bmi)
            if bmi_val >= 30:
                insights.append('A structured weight management plan may improve insulin sensitivity.')
        except Exception:
            pass

    return answer, insights


def _table_has_column(table_name, column_name):
    """Check whether a SQLite table has a given column."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(f'PRAGMA table_info({table_name})')
        return any(row['name'] == column_name for row in cursor.fetchall())
    finally:
        conn.close()

@wellness_bp.route('/doctors/available', methods=['GET'])
def get_available_doctors():
    """Get list of available doctors (mock data)"""
    doctors = [
        {
            'id': 1,
            'name': 'Dr. John Smith',
            'specialization': 'Endocrinology',
            'bio': 'Board-certified endocrinologist with 15+ years experience',
            'degree': 'MD, PhD (Endocrinology)',
            'image_url': 'https://randomuser.me/api/portraits/men/32.jpg',
            'availability': ['Monday', 'Wednesday', 'Friday'],
            'session_price': 120
        },
        {
            'id': 2,
            'name': 'Dr. Priya Patel',
            'specialization': 'Internal Medicine',
            'bio': 'Expert in diabetes management and preventive care',
            'degree': 'MD (Internal Medicine)',
            'image_url': 'https://randomuser.me/api/portraits/women/44.jpg',
            'availability': ['Tuesday', 'Thursday'],
            'session_price': 110
        },
        {
            'id': 3,
            'name': 'Dr. Michael Lee',
            'specialization': 'Family Medicine',
            'bio': 'Experienced family physician with a focus on chronic disease',
            'degree': 'MD (Family Medicine)',
            'image_url': 'https://randomuser.me/api/portraits/men/65.jpg',
            'availability': ['Monday', 'Friday'],
            'session_price': 100
        }
    ]
    return jsonify({
        'status': 'success',
        'doctors': doctors,
        'count': len(doctors)
    }), 200
@wellness_bp.route('/meal-plans', methods=['GET'])
def get_meal_plans():
    """Get meal plans, personalized by user risk level if available"""
    try:
        user_id = session.get('user_id')
        conn = get_db_connection()
        cursor = conn.cursor()

        # Try to get latest risk assessment for personalization
        risk_level = None
        if user_id:
            cursor.execute('''
                SELECT prediction FROM risk_assessments
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id,))
            latest = cursor.fetchone()
            if latest:
                risk_level = latest['prediction']

        # Personalize meal plans if risk_level is available
        if risk_level:
            if risk_level == 'Diabetic':
                cursor.execute('''
                    SELECT * FROM meal_plans WHERE target_audience LIKE '%Diabetic%'
                ''')
            elif risk_level == 'Pre-diabetic':
                cursor.execute('''
                    SELECT * FROM meal_plans WHERE target_audience LIKE '%Pre-diabetic%' OR target_audience LIKE '%All risk%'
                ''')
            else:
                cursor.execute('''
                    SELECT * FROM meal_plans WHERE target_audience LIKE '%All risk%'
                ''')
        else:
            cursor.execute('SELECT * FROM meal_plans')

        meal_plans = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'status': 'success', 'meal_plans': meal_plans, 'personalized': bool(risk_level)}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@wellness_bp.route('/risk-assessment', methods=['POST'])
def create_risk_assessment():
    """Create and persist a risk assessment for the logged-in user."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401

        data = request.get_json() or {}
        assessment_data = {
            'pregnancies': float(data.get('pregnancies', 0)),
            'gender': (data.get('gender') or '').strip(),
            'glucose': float(data.get('glucose', 0)),
            'blood_pressure': float(data.get('blood_pressure', 0)),
            'skin_thickness': float(data.get('skin_thickness', 0)),
            'insulin': float(data.get('insulin', 0)),
            'bmi': float(data.get('bmi', 0)),
            'diabetes_pedigree': float(data.get('diabetes_pedigree', 0)),
            'age': float(data.get('age', 0))
        }

        if diabetes_routes.model is None or diabetes_routes.scaler is None:
            return jsonify({'status': 'error', 'message': 'Model not available'}), 500

        features = np.array([
            assessment_data['pregnancies'],
            assessment_data['glucose'],
            assessment_data['blood_pressure'],
            assessment_data['skin_thickness'],
            assessment_data['insulin'],
            assessment_data['bmi'],
            assessment_data['diabetes_pedigree'],
            assessment_data['age']
        ]).reshape(1, -1)

        features_scaled = diabetes_routes.scaler.transform(features)
        prediction_value = int(diabetes_routes.model.predict(features_scaled)[0])

        # Persist diabetic-class probability so risk bands remain consistent.
        try:
            confidence = _diabetes_probability(diabetes_routes.model, features_scaled)
        except Exception:
            confidence = None

        # Derive model risk band from confidence and apply clinical floor to decide final risk
        try:
            if confidence is None:
                model_risk = 'medium' if prediction_value == 1 else 'low'
            else:
                if confidence >= 0.75:
                    model_risk = 'high'
                elif confidence >= 0.45:
                    model_risk = 'medium'
                else:
                    model_risk = 'low'

            clinical = _clinical_risk_floor(assessment_data)
            rank = {'low': 1, 'medium': 2, 'high': 3}
            final_risk = clinical if rank[clinical] > rank[model_risk] else model_risk

            # Store canonical prediction text so admin counts remain simple
            stored_prediction = 'Diabetic' if final_risk in ('high', 'medium') else 'Non-Diabetic'
        except Exception:
            final_risk = _risk_band(prediction_value, confidence)
            stored_prediction = 'Diabetic' if final_risk in ('high', 'medium') else 'Non-Diabetic'

        conn = get_db_connection()
        cursor = conn.cursor()
        has_gender_column = _table_has_column('risk_assessments', 'gender')
        if has_gender_column:
            cursor.execute('''
                INSERT INTO risk_assessments
                (user_id, pregnancies, gender, glucose, blood_pressure, skin_thickness,
                 insulin, bmi, diabetes_pedigree, age, prediction, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                int(assessment_data['pregnancies']),
                assessment_data['gender'],
                int(assessment_data['glucose']),
                int(assessment_data['blood_pressure']),
                int(assessment_data['skin_thickness']),
                int(assessment_data['insulin']),
                assessment_data['bmi'],
                assessment_data['diabetes_pedigree'],
                int(assessment_data['age']),
                stored_prediction,
                confidence
            ))
        else:
            cursor.execute('''
                INSERT INTO risk_assessments
                (user_id, pregnancies, glucose, blood_pressure, skin_thickness,
                 insulin, bmi, diabetes_pedigree, age, prediction, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                int(assessment_data['pregnancies']),
                int(assessment_data['glucose']),
                int(assessment_data['blood_pressure']),
                int(assessment_data['skin_thickness']),
                int(assessment_data['insulin']),
                assessment_data['bmi'],
                assessment_data['diabetes_pedigree'],
                int(assessment_data['age']),
                stored_prediction,
                confidence
            ))
        conn.commit()
        assessment_id = cursor.lastrowid
        conn.close()

        readable = diabetes_routes._readable_prediction_label(final_risk)

        return jsonify({
            'status': 'success',
            'message': 'Risk assessment saved',
            'assessment_id': assessment_id,
            'prediction': stored_prediction,
            'readable_prediction': readable,
            'prediction_value': prediction_value,
            'confidence': confidence,
            'risk_level': final_risk
        }), 201

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@wellness_bp.route('/risk-assessment/history', methods=['GET'])
def get_risk_history():
    """Get user's risk assessment history"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM risk_assessments
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        assessments = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'assessments': assessments,
            'count': len(assessments)
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@wellness_bp.route('/risk-assessment/latest', methods=['GET'])
def get_latest_assessment():
    """Get user's latest risk assessment"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM risk_assessments
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,))
        
        assessment = cursor.fetchone()
        conn.close()
        
        if not assessment:
            return jsonify({'status': 'error', 'message': 'No assessment found'}), 404
        
        return jsonify({
            'status': 'success',
            'assessment': dict(assessment)
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@wellness_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """Get product recommendations based on latest risk assessment"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest assessment
        cursor.execute('''
            SELECT prediction FROM risk_assessments
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (user_id,))
        
        latest = cursor.fetchone()
        
        if not latest:
            # If no assessment, show all products
            cursor.execute('SELECT * FROM products')
            products = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return jsonify({
                'status': 'success',
                'message': 'Complete product catalog (no risk assessment found)',
                'products': products,
                'risk_level': 'unknown'
            }), 200
        
        prediction = latest['prediction']
        
        # Get recommended products based on risk level
        if prediction == 'Diabetic':
            # Show diabetes-specific products
            cursor.execute('''
                SELECT * FROM products
                WHERE recommended_for LIKE '%Diabetic%'
            ''')
        else:
            # Show prevention products
            cursor.execute('''
                SELECT * FROM products
                WHERE recommended_for LIKE '%Pre-diabetic%' OR recommended_for LIKE '%All risk%'
            ''')
        
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'status': 'success',
            'prediction': prediction,
            'recommended_products': products,
            'risk_level': 'high' if prediction == 'Diabetic' else 'medium' if prediction == 'Pre-diabetic' else 'low'
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@wellness_bp.route('/nutritionist/book', methods=['POST'])
def book_nutritionist():
    """Book a consultation with a nutritionist"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        data = request.get_json() or {}
        nutritionist_name = data.get('nutritionist_name', 'Available Nutritionist').strip()
        booking_date = data.get('booking_date')
        duration = data.get('duration_minutes', 30)
        notes = data.get('notes', '')
        
        if not booking_date:
            return jsonify({'status': 'error', 'message': 'Booking date required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO nutritionist_bookings 
            (user_id, nutritionist_name, booking_date, duration_minutes, notes, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (user_id, nutritionist_name, booking_date, duration, notes))
        
        conn.commit()
        booking_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Booking confirmed',
            'booking_id': booking_id,
            'booking_date': booking_date,
            'nutritionist': nutritionist_name
        }), 201
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@wellness_bp.route('/nutritionist/bookings', methods=['GET'])
def get_bookings():
    """Get user's nutritionist bookings"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM nutritionist_bookings
            WHERE user_id = ?
            ORDER BY booking_date DESC
        ''', (user_id,))
        
        bookings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'status': 'success',
            'bookings': bookings,
            'count': len(bookings)
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@wellness_bp.route('/nutritionist/available', methods=['GET'])
def get_available_nutritionists():
    """Get list of available nutritionists (mock data)"""
    nutritionists = [
        {
            'id': 1,
            'name': 'Dr. Sarah Johnson',
            'specialization': 'Diabetes Management',
            'bio': 'Certified Diabetes Educator with 10+ years experience',
            'availability': ['Monday', 'Tuesday', 'Wednesday'],
            'session_price': 75
        },
        {
            'id': 2,
            'name': 'Ms. Emily Chen',
            'specialization': 'Preventive Nutrition',
            'bio': 'Registered Dietitian Nutritionist',
            'availability': ['Tuesday', 'Thursday', 'Friday'],
            'session_price': 65
        },
        {
            'id': 3,
            'name': 'Mr. David Martinez',
            'specialization': 'Sports & Clinical Nutrition',
            'bio': 'Board-certified specialist in clinical nutrition',
            'availability': ['Monday', 'Wednesday', 'Friday'],
            'session_price': 85
        }
    ]
    
    return jsonify({
        'status': 'success',
        'nutritionists': nutritionists,
        'count': len(nutritionists)
    }), 200


@wellness_bp.route('/chatbot', methods=['POST'])
def chatbot():
    """Lightweight rule-based assistant for diabetes Q&A and result explanation."""
    try:
        data = request.get_json() or {}
        question = (data.get('question') or '').strip().lower()
        risk_level = (data.get('risk_level') or '').strip().lower()
        glucose = data.get('glucose')
        bmi = data.get('bmi')
        chat_history = _normalize_chat_history(data.get('messages'))

        if not question:
            return jsonify({'status': 'error', 'message': 'Question is required'}), 400

        answer, insights = _compose_chatbot_reply(
            question,
            risk_level=risk_level,
            glucose=glucose,
            bmi=bmi,
            chat_history=chat_history
        )

        return jsonify({
            'status': 'success',
            'answer': answer,
            'insights': insights
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@wellness_bp.route('/admin/overview', methods=['GET'])
def admin_overview():
    """Return lightweight admin metrics and storage overview."""
    import traceback
    import json
    
    print("\n[ADMIN] Starting admin_overview request...")
    
    try:
        user_id = session.get('user_id')
        print(f"[ADMIN] User ID from session: {user_id}")
        
        if not user_id:
            print("[ADMIN] No user_id in session, returning 401")
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check admin status
        cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
        viewer = cursor.fetchone()
        print(f"[ADMIN] Viewer data: {viewer}")
        
        if not viewer or int(viewer['is_admin'] or 0) != 1:
            conn.close()
            print("[ADMIN] User is not admin, returning 403")
            return jsonify({'status': 'error', 'message': 'Admin access required'}), 403

        print("[ADMIN] User is admin, proceeding...")

        # Get basic metrics
        cursor.execute('SELECT COUNT(*) AS total_users FROM users')
        total_users = int(cursor.fetchone()['total_users'])

        cursor.execute('SELECT COUNT(*) AS total_assessments FROM risk_assessments')
        total_assessments = int(cursor.fetchone()['total_assessments'])

        cursor.execute('SELECT COUNT(*) AS diabetic_count FROM risk_assessments WHERE prediction = ?', ('Diabetic',))
        diabetic_count = int(cursor.fetchone()['diabetic_count'])

        cursor.execute('SELECT COUNT(*) AS booking_count FROM nutritionist_bookings')
        booking_count = int(cursor.fetchone()['booking_count'])

        print(f"[ADMIN] Metrics: users={total_users}, assessments={total_assessments}, diabetic={diabetic_count}")

        # Recent authentication activity
        cursor.execute('''
            SELECT id, user_id, username, event_type, status, ip_address, created_at
            FROM auth_activity_logs
            ORDER BY created_at DESC
            LIMIT 20
        ''')
        recent_auth_activity = []
        for row in cursor.fetchall():
            recent_auth_activity.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'username': row['username'],
                'event_type': row['event_type'],
                'status': row['status'],
                'ip_address': row['ip_address'],
                'created_at': str(row['created_at'])
            })

        # Recent assessments
        cursor.execute('''
            SELECT id, user_id, prediction, confidence, created_at
            FROM risk_assessments
            ORDER BY created_at DESC
            LIMIT 8
        ''')
        recent_assessments = []
        for row in cursor.fetchall():
            recent_assessments.append({
                'id': row['id'],
                'user_id': row['user_id'],
                'prediction': row['prediction'],
                'confidence': float(row['confidence']) if row['confidence'] else None,
                'created_at': str(row['created_at'])
            })

        # Trend data - SIMPLIFIED to avoid JSON issues
        cursor.execute('''
            SELECT DATE(created_at) AS day,
                   COUNT(*) AS total,
                   SUM(CASE WHEN prediction = 'Diabetic' THEN 1 ELSE 0 END) AS diabetic
            FROM risk_assessments
            WHERE created_at >= DATETIME('now', '-14 days')
            GROUP BY DATE(created_at)
            ORDER BY day ASC
        ''')
        trends = []
        for row in cursor.fetchall():
            trends.append({
                'day': str(row['day']) if row['day'] else None,
                'total': int(row['total']) if row['total'] else 0,
                'diabetic': int(row['diabetic']) if row['diabetic'] else 0
            })

        # Detailed user data query with latest assessment
        cursor.execute('''
            SELECT
                u.id,
                u.username,
                u.email,
                u.full_name,
                u.age,
                (SELECT gender FROM risk_assessments WHERE user_id = u.id ORDER BY created_at DESC LIMIT 1) AS latest_gender,
                COUNT(ra.id) AS assessment_count,
                SUM(CASE WHEN ra.prediction = 'Diabetic' THEN 1 ELSE 0 END) AS diabetic_count,
                (SELECT prediction FROM risk_assessments WHERE user_id = u.id ORDER BY created_at DESC LIMIT 1) AS latest_prediction,
                (SELECT confidence FROM risk_assessments WHERE user_id = u.id ORDER BY created_at DESC LIMIT 1) AS latest_confidence,
                (SELECT glucose FROM risk_assessments WHERE user_id = u.id ORDER BY created_at DESC LIMIT 1) AS latest_glucose,
                (SELECT bmi FROM risk_assessments WHERE user_id = u.id ORDER BY created_at DESC LIMIT 1) AS latest_bmi,
                (SELECT MAX(created_at) FROM risk_assessments WHERE user_id = u.id) AS last_assessment_date,
                COUNT(nb.id) AS booking_count
            FROM users u
            LEFT JOIN risk_assessments ra ON ra.user_id = u.id
            LEFT JOIN nutritionist_bookings nb ON nb.user_id = u.id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        ''')
        users_list = []
        for row in cursor.fetchall():
            latest_raw = row['latest_prediction']
            latest_gender = row['latest_gender'] or 'N/A'
            latest_conf = float(row['latest_confidence']) if row['latest_confidence'] else None
            latest_gluc = float(row['latest_glucose']) if row['latest_glucose'] else None
            latest_bmi = float(row['latest_bmi']) if row['latest_bmi'] else None

            # Derive readable latest prediction using confidence and clinical floor
            try:
                if latest_conf is None:
                    model_risk = 'medium' if latest_raw == 'Diabetic' else 'low'
                else:
                    if latest_conf >= 0.75:
                        model_risk = 'high'
                    elif latest_conf >= 0.45:
                        model_risk = 'medium'
                    else:
                        model_risk = 'low'

                clinical = _clinical_risk_floor({'glucose': latest_gluc or 0, 'bmi': latest_bmi or 0, 'age': row['age'] or 0, 'diabetes_pedigree': 0, 'insulin': 0})
                rank = {'low': 1, 'medium': 2, 'high': 3}
                final_risk = clinical if rank[clinical] > rank[model_risk] else model_risk
                latest_readable = diabetes_routes._readable_prediction_label(final_risk)
            except Exception:
                latest_readable = latest_raw or 'N/A'

            users_list.append({
                'id': row['id'],
                'username': row['username'],
                'email': row['email'],
                'full_name': row['full_name'],
                'age': row['age'],
                'latest_gender': latest_gender,
                'assessment_count': int(row['assessment_count']) if row['assessment_count'] else 0,
                'diabetic_count': int(row['diabetic_count']) if row['diabetic_count'] else 0,
                'latest_prediction': latest_readable,
                'latest_confidence': latest_conf,
                'latest_glucose': latest_gluc,
                'latest_bmi': latest_bmi,
                'last_assessment_date': str(row['last_assessment_date']) if row['last_assessment_date'] else 'No records',
                'booking_count': int(row['booking_count']) if row['booking_count'] else 0
            })

        print(f"[ADMIN] Processed {len(users_list)} users and {len(trends)} trend days")

        db_size_mb = 0.0
        db_path_str = str(DB_PATH)
        try:
            db_size_mb = round(float(os.path.getsize(db_path_str)) / (1024 * 1024), 3)
        except Exception as e:
            print(f"[ADMIN] Error getting DB size: {e}")
            db_size_mb = 0.0

        response_data = {
            'status': 'success',
            'overview': {
                'total_users': total_users,
                'total_assessments': total_assessments,
                'diabetic_assessments': diabetic_count,
                'non_diabetic_assessments': max(total_assessments - diabetic_count, 0),
                'nutritionist_bookings': booking_count
            },
            'storage': {
                'database_type': 'SQLite',
                'database_path': db_path_str,
                'database_size_mb': db_size_mb,
                'tables': ['users', 'risk_assessments', 'products', 'cart_items', 'orders', 'order_items', 'nutritionist_bookings', 'meal_plans', 'auth_activity_logs']
            },
            'trends': trends,
            'users_data': users_list,
            'recent_assessments': recent_assessments,
            'recent_auth_activity': recent_auth_activity,
            'viewer': {'user_id': user_id}
        }
        
        # Test JSON serialization
        json_test = json.dumps(response_data)
        print(f"[ADMIN] Response is JSON-serializable ({len(json_test)} bytes)")
        
        conn.close()
        print("[ADMIN] Returning 200 with admin data")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"[ADMIN] ERROR: {str(e)}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500
