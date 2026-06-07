from flask import Blueprint, request, jsonify
from db import get_db
import time
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    db = get_db()

    patient_id = "P-" + str(uuid.uuid4())[:6].upper()
    patient = {
        "_id": patient_id,
        "name": body.get('name'),
        "age": body.get('age'),
        "blood_group": body.get('blood_group'),
        "conditions": body.get('conditions'),
        "phone": body.get('phone'),
        "email": body.get('email'),
        "password": body.get('password'), # Mock auth: plaintext
        "role": "patient",
        "created_at": time.time()
    }

    # Check if user already exists
    if db.patients.find_one({"$or": [{"phone": patient['phone']}, {"email": patient['email']}]}):
        return jsonify({"error": "User with this phone or email already exists"}), 400

    db.patients.insert_one(patient)

    # Return user without password
    user_data = {k: v for k, v in patient.items() if k != 'password'}
    user_data['id'] = user_data.pop('_id')

    return jsonify({
        "message": "Signup successful",
        "user": user_data
    }), 201

@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    user_id = body.get('user') # Phone or Email
    password = body.get('password')

    if not isinstance(user_id, str) or not isinstance(password, str):
        return jsonify({"error": "Invalid input format"}), 400

    db = get_db()
    patient = db.patients.find_one({
        "$or": [{"phone": user_id}, {"email": user_id}],
        "password": password
    })

    if not patient:
        return jsonify({"error": "Invalid credentials"}), 401

    user_data = {k: v for k, v in patient.items() if k != 'password'}
    user_data['id'] = user_data.pop('_id')
    
    return jsonify({
        "message": "Login successful",
        "user": user_data
    })

@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    # Hospital Name, Doctor ID or Email, Password, Hospital Code
    hospital_name = body.get('hospital_name')
    user_id = body.get('user')
    password = body.get('password')
    hospital_code = body.get('hospital_code')

    # Mock hospital login
    # For prototype, we just accept if all fields are present
    if not all([hospital_name, user_id, password, hospital_code]):
        return jsonify({"error": "All fields are required"}), 400

    user = {
        "id": user_id,
        "name": hospital_name,
        "hospital_code": hospital_code,
        "role": "hospital"
    }

    return jsonify({
        "message": "Hospital login successful",
        "user": user
    })
