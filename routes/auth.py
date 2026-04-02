from flask import Blueprint, request, jsonify
from db import get_db
import time
import os
import jwt

auth_bp = Blueprint('auth', __name__)

SECRET_KEY = os.environ.get("JWT_SECRET", "mediqueue-secret-123")

@auth_bp.route('/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for field in required:
        if not body.get(field):
            return jsonify({"error": f"Field {field} is required"}), 400

    db = get_db()
    if db.users.find_one({"$or": [{"phone": body['phone']}, {"email": body['email']}], "role": "patient"}):
        return jsonify({"error": "Patient already exists"}), 400

    user_id = f"P-{int(time.time())}"
    user = {
        "_id": user_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('conditions', ''),
        "phone": body['phone'],
        "email": body['email'],
        "password": body['password'], # In a real app, hash this
        "role": "patient",
        "created_at": time.time()
    }
    db.users.insert_one(user)

    token = jwt.encode({"user_id": user_id, "role": "patient"}, SECRET_KEY, algorithm="HS256")
    user.pop('password')
    user['id'] = user.pop('_id')

    return jsonify({"message": "Signup successful", "token": token, "user": user}), 201

@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    identifier = body.get('identifier') # phone or email
    password = body.get('password')

    if not identifier or not password:
        return jsonify({"error": "Identifier and password are required"}), 400

    db = get_db()
    user = db.users.find_one({
        "$or": [{"phone": identifier}, {"email": identifier}],
        "password": password,
        "role": "patient"
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({"user_id": user['_id'], "role": "patient"}, SECRET_KEY, algorithm="HS256")
    user.pop('password')
    user['id'] = user.pop('_id')
    return jsonify({"message": "Login successful", "token": token, "user": user})

@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    required = ['hospital_name', 'doctor_id', 'hospital_code', 'password']
    for field in required:
        if not body.get(field):
            return jsonify({"error": f"Field {field} is required"}), 400

    # For prototype, we accept any valid-looking credentials
    # In a real app, we would verify against a hospitals/doctors collection
    token = jwt.encode({
        "hospital_code": body['hospital_code'],
        "doctor_id": body['doctor_id'],
        "role": "hospital"
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "name": body['doctor_id'],
            "hospital": body['hospital_name'],
            "hospitalCode": body['hospital_code'],
            "role": "hospital"
        }
    })
