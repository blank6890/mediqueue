from flask import Blueprint, request, jsonify
from db import get_db
import time
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    db = get_db()

    # Required fields: Full Name, Age, Blood Group, Chronic Conditions, Phone Number, Email, Password
    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for f in required:
        if f not in body:
            return jsonify({"error": f"Missing field: {f}"}), 400

    # Check if user already exists
    if db.users.find_one({"$or": [{"phone": body['phone']}, {"email": body['email']}], "role": "patient"}):
        return jsonify({"error": "User already exists"}), 400

    user_id = "P-" + str(uuid.uuid4())[:8].upper()
    user = {
        "_id": user_id,
        "role": "patient",
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('conditions', ''),
        "phone": body['phone'],
        "email": body['email'],
        "password": body['password'], # In a real app, hash this!
        "created_at": time.time()
    }

    db.users.insert_one(user)

    # Also create a patient record in patients collection for compatibility with existing routes
    patient_record = {
        "_id": user_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('conditions', ''),
        "phone": body['phone'],
        "lat": 17.3850,
        "lng": 78.4867
    }
    db.patients.insert_one(patient_record)

    user_data = {k: v for k, v in user.items() if k != 'password'}
    user_data['id'] = user_data.pop('_id')

    return jsonify({"message": "Signup successful", "user": user_data}), 201

@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    db = get_db()
    
    user_input = body.get('user') # Phone or Email
    password = body.get('password')

    if not user_input or not password:
        return jsonify({"error": "User and password required"}), 400

    user = db.users.find_one({
        "$or": [{"phone": user_input}, {"email": user_input}],
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
    db = get_db()

    # Login fields: Hospital Name, Doctor ID or Email, Password
    # Add a "Hospital Code" field (e.g. HOSP-001) that links the doctor to a hospital
    h_name = body.get('hospital_name')
    user_input = body.get('user') # Doctor ID or Email
    h_code = body.get('hospital_code')
    password = body.get('password')

    if not all([h_name, user_input, h_code, password]):
        return jsonify({"error": "All fields are required"}), 400

    # Mock hospital login for prototype
    # In a real app, we would verify against a hospitals and hospital_staff collection
    user_id = "D-" + str(uuid.uuid4())[:8].upper()
    user_data = {
        "id": user_id,
        "role": "hospital",
        "name": h_name,
        "doctor_id": user_input,
        "hospital_code": h_code
    }

    return jsonify({"message": "Login successful", "user": user_data})
