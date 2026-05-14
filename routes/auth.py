from flask import Blueprint, request, jsonify, session
from db import get_db
import time
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for f in required:
        if f not in body:
            return jsonify({"error": f"Missing field: {f}"}), 400

    db = get_db()
    # Check if user exists
    if db.users.find_one({"$or": [{"phone": body['phone']}, {"email": body['email']}], "role": "patient"}):
        return jsonify({"error": "User with this phone or email already exists"}), 400

    user = {
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('conditions', ''),
        "phone": body['phone'],
        "email": body['email'],
        "password": body['password'], # In a real app, hash this!
        "role": "patient",
        "created_at": time.time()
    }
    result = db.users.insert_one(user)
    user['id'] = str(result.inserted_id)
    user.pop('_id')
    user.pop('password')
    return jsonify({"message": "Signup successful", "user": user}), 201

@auth_bp.route('/api/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    identifier = body.get('identifier') # phone or email
    password = body.get('password')

    if not identifier or not password:
        return jsonify({"error": "Identifier and password required"}), 400

    db = get_db()
    user = db.users.find_one({
        "$or": [{"phone": identifier}, {"email": identifier}],
        "password": password,
        "role": "patient"
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = str(user.pop('_id'))
    user.pop('password')
    return jsonify({"message": "Login successful", "user": user})

@auth_bp.route('/api/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    required = ['hospital_name', 'identifier', 'password', 'hospital_code']
    for f in required:
        if f not in body:
            return jsonify({"error": f"Missing field: {f}"}), 400

    # For prototype, we can just accept any login that matches these if we don't have a hospital user DB
    # or we can check against a simple "doctors" or "hospital_staff" collection.
    # The requirement says "Store login state in localStorage".
    
    db = get_db()
    # Let's see if we have this hospital
    # Actually, let's just mock/simple-auth for prototype as requested "or mock auth for prototype"

    user = {
        "hospital_name": body['hospital_name'],
        "doctor_id": body['identifier'],
        "hospital_code": body['hospital_code'],
        "role": "hospital"
    }

    # Optionally store in DB if needed, but for prototype mock is fine.
    # However, let's at least check if the hospital code exists in our HOSPITALS list.
    from routes.hospitals import HOSPITALS
    hospital = next((h for h in HOSPITALS if h['id'] == body['hospital_code']), None)

    if not hospital:
        return jsonify({"error": "Invalid Hospital Code"}), 401

    user['hospital_id'] = hospital['id']

    return jsonify({"message": "Hospital login successful", "user": user})

@auth_bp.route('/get-user/<phone>/<role>', methods=['GET'])
def get_user(phone, role):
    db = get_db()
    user = db.users.find_one({"phone": phone, "role": role})
    if not user:
        return jsonify({"error": "User not found"}), 404
    user['id'] = str(user.pop('_id'))
    if 'password' in user: user.pop('password')
    return jsonify(user)
