from flask import Blueprint, request, jsonify
from db import get_db
import time
import os

auth_bp = Blueprint('auth', __name__)

# Mock auth for prototype
@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    identifier = body.get('identifier') # phone or email
    password = body.get('password')

    if not identifier or not password:
        return jsonify({"error": "identifier and password are required"}), 400

    db = get_db()
    user = db.patients.find_one({
        "$and": [
            {"$or": [{"phone": identifier}, {"email": identifier}]},
            {"password": password}
        ]
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = user.pop('_id')
    if 'password' in user:
        del user['password']
    user['role'] = 'patient'

    return jsonify({
        "message": "Login successful",
        "user": user
    })

@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    hospital_name = body.get('hospital_name')
    doctor_identifier = body.get('doctor_identifier') # ID or email
    hospital_code = body.get('hospital_code')
    password = body.get('password')

    if not all([hospital_name, doctor_identifier, hospital_code, password]):
        return jsonify({"error": "All fields are required"}), 400

    # For prototype, we'll just return a mock user if fields are provided
    # In a real app, we would validate against a hospitals/doctors collection
    user = {
        "id": "DOC-" + doctor_identifier[:4].upper() if len(doctor_identifier) > 4 else "DOC-1234",
        "name": hospital_name,
        "doctor": doctor_identifier,
        "hospital_code": hospital_code,
        "role": "hospital"
    }

    return jsonify({
        "message": "Login successful",
        "user": user
    })

# Keeping existing OTP routes for backward compatibility if needed,
# though the new flow uses password-based login for now.
@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    # ... existing implementation ...
    return jsonify({"message": "OTP flow is deprecated for password-based login in this version"}), 501
