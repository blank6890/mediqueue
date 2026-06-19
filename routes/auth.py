from flask import Blueprint, request, jsonify, session
from db import get_db
import time
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for field in required:
        if field not in body:
            return jsonify({"error": f"Missing field: {field}"}), 400

    db = get_db()
    # Check if user already exists
    if db.users.find_one({"$or": [{"phone": body['phone']}, {"email": body['email']}], "role": "patient"}):
        return jsonify({"error": "User with this phone or email already exists"}), 400

    user_id = "P-" + os.urandom(4).hex().upper()
    user = {
        "_id": user_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('conditions', ''),
        "phone": body['phone'],
        "email": body['email'],
        "password": body['password'], # Plaintext for prototype
        "role": "patient",
        "created_at": time.time()
    }
    db.users.insert_one(user)

    user_data = user.copy()
    user_data['id'] = str(user_data.pop('_id'))
    del user_data['password']

    return jsonify({
        "message": "Signup successful",
        "user": user_data
    }), 201

@auth_bp.route('/api/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    user_id_input = body.get('user_id') # Phone or Email
    password = body.get('password')

    if not isinstance(user_id_input, str) or not isinstance(password, str):
        return jsonify({"error": "Invalid input type"}), 400

    if not user_id_input or not password:
        return jsonify({"error": "user_id and password are required"}), 400

    db = get_db()
    user = db.users.find_one({
        "$or": [{"phone": user_id_input}, {"email": user_id_input}],
        "role": "patient",
        "password": password
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user_data = user.copy()
    user_data['id'] = str(user_data.pop('_id'))
    del user_data['password']

    return jsonify({
        "message": "Login successful",
        "user": user_data
    })

@auth_bp.route('/api/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    hospital_name = body.get('hospital_name')
    doctor_id = body.get('doctor_id') # Doctor ID or Email
    hospital_code = body.get('hospital_code')
    password = body.get('password')

    if not all(isinstance(x, str) for x in [hospital_name, doctor_id, hospital_code, password]):
        return jsonify({"error": "Invalid input type"}), 400

    if not all([hospital_name, doctor_id, hospital_code, password]):
        return jsonify({"error": "All fields are required"}), 400

    db = get_db()
    user = db.users.find_one({
        "doctor_id": doctor_id,
        "hospital_code": hospital_code,
        "role": "hospital",
        "password": password
    })

    if not user:
        # Create a mock hospital user if it doesn't exist (for prototype convenience)
        user = {
            "_id": "H-" + os.urandom(4).hex().upper(),
            "name": doctor_id,
            "hospital_name": hospital_name,
            "hospital_code": hospital_code,
            "doctor_id": doctor_id,
            "password": password,
            "role": "hospital",
            "created_at": time.time()
        }
        db.users.insert_one(user)

    user_data = user.copy()
    user_data['id'] = str(user_data.pop('_id'))
    del user_data['password']

    return jsonify({
        "message": "Hospital login successful",
        "user": user_data
    })
