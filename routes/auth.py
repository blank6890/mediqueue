from flask import Blueprint, request, jsonify
from db import get_db
import time
import uuid

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for f in required:
        if f not in body:
            return jsonify({"error": f"Missing field: {f}"}), 400

    db = get_db()
    # Check if user already exists
    if db.patients.find_one({"$or": [{"phone": body['phone']}, {"email": body['email']}]}):
        return jsonify({"error": "User already exists with this phone or email"}), 400

    patient_id = "P-" + str(uuid.uuid4())[:8].upper()
    patient = {
        "_id": patient_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('conditions', ''),
        "phone": body['phone'],
        "email": body['email'],
        "password": body['password'], # Plaintext for prototype
        "created_at": time.time(),
        "role": "patient"
    }
    db.patients.insert_one(patient)

    return jsonify({
        "message": "Signup successful",
        "user": {
            "id": patient_id,
            "name": patient['name'],
            "role": "patient"
        }
    }), 201

@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    user_id = body.get('user_id') # email or phone
    password = body.get('password')

    if not user_id or not password:
        return jsonify({"error": "user_id and password are required"}), 400

    db = get_db()
    user = db.patients.find_one({
        "$or": [{"phone": user_id}, {"email": user_id}],
        "password": password
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user["_id"],
            "name": user["name"],
            "role": "patient"
        }
    })

@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    h_name = body.get('hospital_name')
    h_user = body.get('user_id') # doctor id or email
    h_code = body.get('hospital_code')
    h_pass = body.get('password')

    if not all([h_name, h_user, h_code, h_pass]):
        return jsonify({"error": "All fields are required"}), 400

    from routes.hospitals import HOSPITALS
    hospital = next((h for h in HOSPITALS if h['id'] == h_code and h['name'] == h_name), None)

    if not hospital:
        return jsonify({"error": "Hospital not found"}), 404

    if hospital['doctor_id'] == h_user and hospital['password'] == h_pass:
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": hospital["id"],
                "name": hospital["name"],
                "role": "hospital",
                "hospitalCode": hospital["id"]
            }
        })
    else:
        return jsonify({"error": "Invalid credentials"}), 401
