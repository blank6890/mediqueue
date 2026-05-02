from flask import Blueprint, request, jsonify, session
from db import get_db
import time
import os
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    name = body.get('name')
    age = body.get('age')
    blood_group = body.get('blood_group')
    conditions = body.get('conditions', '')
    phone = body.get('phone')
    email = body.get('email')
    password = body.get('password')

    if not all([name, age, blood_group, phone, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    db = get_db()
    if db.users.find_one({"$or": [{"phone": phone}, {"email": email}]}):
        return jsonify({"error": "User already exists with this phone or email"}), 400

    user_id = "P-" + str(uuid.uuid4())[:6].upper()
    user = {
        "_id": user_id,
        "name": name,
        "age": age,
        "blood_group": blood_group,
        "conditions": conditions,
        "phone": phone,
        "email": email,
        "password": password,
        "role": "patient",
        "created_at": time.time()
    }
    db.users.insert_one(user)

    # Compatibility with patients collection
    db.patients.insert_one({
        "_id": user_id,
        "name": name,
        "age": age,
        "blood_group": blood_group,
        "conditions": conditions,
        "phone": phone,
        "lat": 17.3850,
        "lng": 78.4867
    })

    user['id'] = str(user.pop('_id'))
    user.pop('password')
    return jsonify({"message": "Signup successful", "user": user}), 201

@auth_bp.route('/api/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    identifier = body.get('identifier')
    password = body.get('password')

    if not identifier or not password:
        return jsonify({"error": "Identifier and password required"}), 400

    db = get_db()
    user = db.users.find_one({
        "$and": [
            {"$or": [{"phone": identifier}, {"email": identifier}]},
            {"role": "patient"}
        ]
    })

    if not user or user.get('password') != password:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = str(user.pop('_id'))
    user.pop('password')
    return jsonify({"message": "Login successful", "user": user})

@auth_bp.route('/api/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    hospital_name = body.get('hospital_name')
    doctor_id = body.get('doctor_id')
    password = body.get('password')
    hospital_code = body.get('hospital_code')

    if not all([hospital_name, doctor_id, password, hospital_code]):
        return jsonify({"error": "Missing required fields"}), 400

    db = get_db()
    user = db.users.find_one({
        "$and": [
            {"$or": [{"doctor_id": doctor_id}, {"email": doctor_id}]},
            {"role": "hospital"},
            {"hospital_code": hospital_code}
        ]
    })

    if not user or user.get('password') != password:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = str(user.pop('_id'))
    user.pop('password', None)
    return jsonify({"message": "Login successful", "user": user})

# Legacy OTP support (kept for internal use if any)
@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    return jsonify({"message": "OTP flow is deprecated. Use password login."}), 410

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    return jsonify({"message": "OTP flow is deprecated. Use password login."}), 410
