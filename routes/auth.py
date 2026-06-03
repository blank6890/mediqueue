from flask import Blueprint, request, jsonify, session
from db import get_db
import time
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    required = ['name', 'age', 'blood_group', 'conditions', 'phone', 'email', 'password']
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
        "conditions": body['conditions'],
        "phone": body['phone'],
        "email": body['email'],
        "password": body['password'], # Prototype: plain text
        "role": "patient",
        "created_at": time.time()
    }
    db.users.insert_one(user)

    # Also create a record in patients collection for compatibility
    db.patients.insert_one({
        "_id": user_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body['conditions'],
        "phone": body['phone'],
        "lat": 17.3850,
        "lng": 78.4867
    })

    user['id'] = user.pop('_id')
    user.pop('password')
    return jsonify({"message": "Signup successful", "user": user}), 201

@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    user_id_or_email = body.get('user') # email or phone
    password = body.get('password')

    if not user_id_or_email or not password:
        return jsonify({"error": "Missing user or password"}), 400

    db = get_db()
    user = db.users.find_one({
        "$or": [{"phone": user_id_or_email}, {"email": user_id_or_email}],
        "password": password,
        "role": "patient"
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = user.pop('_id')
    user.pop('password')
    return jsonify({"message": "Login successful", "user": user})

@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    hospital_name = body.get('hospital_name')
    user_id_or_email = body.get('user')
    hospital_code = body.get('hospital_code')
    password = body.get('password')

    if not hospital_name or not user_id_or_email or not hospital_code or not password:
        return jsonify({"error": "Missing fields"}), 400

    # Prototype: simple mock check or store in db
    db = get_db()
    user = db.users.find_one({
        "hospital_code": hospital_code,
        "role": "hospital"
    })

    if not user:
        # For prototype, create it if it doesn't exist
        user_id = "H-" + hospital_code
        user = {
            "_id": user_id,
            "hospital_name": hospital_name,
            "doctor_user": user_id_or_email,
            "hospital_code": hospital_code,
            "password": password,
            "role": "hospital",
            "created_at": time.time()
        }
        db.users.insert_one(user)
    elif user['password'] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = user.pop('_id')
    user.pop('password')
    return jsonify({"message": "Login successful", "user": user})
