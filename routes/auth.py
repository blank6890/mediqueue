from flask import Blueprint, request, jsonify
from db import get_db
import time
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for field in required:
        if field not in body:
            return jsonify({"error": f"Missing field: {field}"}), 400

    db = get_db()
    # Check if user already exists
    if db.users.find_one({"$or": [{"phone": body['phone']}, {"email": body['email']}], "role": "patient"}):
        return jsonify({"error": "Patient already exists with this phone or email"}), 400

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

    # Also register as a patient in the patients collection for compatibility with existing logic
    db.patients.insert_one({
        "_id": user_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('conditions', ''),
        "phone": body['phone'],
        "lat": 17.3850,
        "lng": 78.4867
    })

    user_data = {k: v for k, v in user.items() if k != 'password'}
    user_data['id'] = user_data.pop('_id')
    return jsonify({"message": "Signup successful", "user": user_data}), 201

@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    user_id_input = body.get('user_id') # email or phone
    password = body.get('password')

    if not user_id_input or not password:
        return jsonify({"error": "User ID and password are required"}), 400

    db = get_db()
    user = db.users.find_one({
        "$or": [{"phone": user_id_input}, {"email": user_id_input}],
        "role": "patient",
        "password": password
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user_data = {k: v for k, v in user.items() if k != 'password'}
    user_data['id'] = user_data.pop('_id')
    return jsonify({"message": "Login successful", "user": user_data})

@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    # Required: Hospital Name, Doctor ID or Email, Password, Hospital Code
    required = ['hospital_name', 'doctor_id', 'password', 'hospital_code']
    for field in required:
        if field not in body:
            return jsonify({"error": f"Missing field: {field}"}), 400

    # For prototype, we accept any login if it's "hospital" role or just mock it
    # Let's just return a success with the provided data for the prototype
    user_data = {
        "id": body['doctor_id'],
        "name": body['hospital_name'],
        "hospital_code": body['hospital_code'],
        "role": "hospital"
    }

    return jsonify({"message": "Login successful", "user": user_data})
