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
    if prediction_value == 1 and confidence is not None and confidence >= 0.8:
        return 'high'
    if prediction_value == 1:
        return 'medium'
    return 'low'

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
            if 'Diabetic' in risk_level:
                cursor.execute('''
                    SELECT * FROM meal_plans WHERE target_audience LIKE '%Diabetic%'
                ''')
            elif 'Pre-diabetic' in risk_level:
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
        prediction = 'Diabetic' if prediction_value == 1 else 'Non-Diabetic'

        confidence = None
        try:
            prob = diabetes_routes.model.predict_proba(features_scaled)
            confidence = float(prob[0][prediction_value])
        except Exception:
            confidence = None

        conn = get_db_connection()
        cursor = conn.cursor()
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
            prediction,
            confidence
        ))
        conn.commit()
        assessment_id = cursor.lastrowid
        conn.close()

        return jsonify({
            'status': 'success',
            'message': 'Risk assessment saved',
            'assessment_id': assessment_id,
            'prediction': prediction,
            'prediction_value': prediction_value,
            'confidence': confidence,
            'risk_level': _risk_band(prediction_value, confidence)
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
        if 'Diabetic' in prediction:
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
            'risk_level': 'high' if 'Diabetic' in prediction else 'medium' if 'Pre-diabetic' in prediction else 'low'
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

        if not question:
            return jsonify({'status': 'error', 'message': 'Question is required'}), 400

        answer = (
            "I can help explain diabetes risk, diet patterns, exercise habits, and how to interpret your score. "
            "Ask a specific question for better guidance."
        )

        if 'result' in question or 'confidence' in question or 'risk' in question:
            if risk_level == 'high':
                answer = (
                    "Your result suggests high risk. Consider speaking with a clinician for confirmatory testing. "
                    "Start with low-glycemic meals, daily walking, and regular glucose tracking."
                )
            elif risk_level == 'medium':
                answer = (
                    "Your result suggests moderate risk. Small consistent changes can help: reduce refined carbs, "
                    "increase fiber/protein, and target 150 minutes of activity per week."
                )
            elif risk_level == 'low':
                answer = (
                    "Your result suggests low risk right now. Keep preventive habits: balanced meals, hydration, "
                    "exercise, and annual screening."
                )

        if 'diet' in question or 'food' in question:
            answer = (
                "Prioritize vegetables, legumes, lean proteins, nuts, and whole grains. "
                "Limit sugary drinks, refined snacks, and oversized portions."
            )

        if 'exercise' in question or 'workout' in question:
            answer = (
                "Aim for 30 minutes of brisk activity on most days, plus 2 strength sessions weekly. "
                "Even post-meal walks can improve glucose response."
            )

        insights = []
        if glucose is not None:
            try:
                glucose_val = float(glucose)
                if glucose_val >= 140:
                    insights.append('Glucose appears elevated; discuss follow-up testing with your doctor.')
            except Exception:
                pass

        if bmi is not None:
            try:
                bmi_val = float(bmi)
                if bmi_val >= 30:
                    insights.append('A structured weight management plan may meaningfully reduce risk.')
            except Exception:
                pass

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

        # Simplified user data query
        cursor.execute('''
            SELECT
                u.id,
                u.username,
                u.email,
                u.full_name,
                u.age,
                COUNT(ra.id) AS assessment_count,
                SUM(CASE WHEN ra.prediction = 'Diabetic' THEN 1 ELSE 0 END) AS diabetic_count
            FROM users u
            LEFT JOIN risk_assessments ra ON ra.user_id = u.id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        ''')
        users_list = []
        for row in cursor.fetchall():
            users_list.append({
                'id': row['id'],
                'username': row['username'],
                'email': row['email'],
                'full_name': row['full_name'],
                'age': row['age'],
                'assessment_count': int(row['assessment_count']) if row['assessment_count'] else 0,
                'diabetic_count': int(row['diabetic_count']) if row['diabetic_count'] else 0
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
                'tables': ['users', 'risk_assessments', 'products', 'cart_items', 'orders', 'order_items', 'nutritionist_bookings', 'meal_plans']
            },
            'trends': trends,
            'users_data': users_list,
            'recent_assessments': recent_assessments,
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
