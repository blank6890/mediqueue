from flask import Blueprint, request, jsonify, session
from db import get_db
from twilio.rest import Client
import random
import time
import os

auth_bp = Blueprint('auth', __name__)

TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN")
TWILIO_PHONE = os.environ.get("TWILIO_PHONE")

twilio = Client(TWILIO_SID, TWILIO_TOKEN)

def generate_otp():
    return str(random.randint(100000, 999999))

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    body = request.get_json()
    phone = body.get('phone')
    role = body.get('role')  # patient, admin, doctor

    if not phone or not role:
        return jsonify({"error": "phone and role are required"}), 400

    if role not in ['patient', 'admin', 'doctor']:
        return jsonify({"error": "Invalid role"}), 400

    otp = generate_otp()
    expires_at = time.time() + 300  # 5 min expiry

    db = get_db()
    db.otp_store.update_one(
        {"phone": phone},
        {"$set": {"phone": phone, "otp": otp, "role": role, "expires_at": expires_at}},
        upsert=True
    )

    try:
        twilio.messages.create(
            body=f"Your MediQueue OTP is: {otp}. Valid for 5 minutes. Do not share this with anyone.",
            from_=TWILIO_PHONE,
            to=phone
        )
        return jsonify({"message": "OTP sent successfully", "phone": phone})
    except Exception as e:
        return jsonify({"error": "Failed to send OTP: " + str(e)}), 500


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    body = request.get_json()
    phone = body.get('phone')
    otp = body.get('otp')
    role = body.get('role')
    name = body.get('name', '')

    if not phone or not otp or not role:
        return jsonify({"error": "phone, otp and role are required"}), 400

    db = get_db()
    record = db.otp_store.find_one({"phone": phone, "role": role})

    if not record:
        return jsonify({"error": "OTP not found. Please request a new one."}), 404

    if time.time() > record['expires_at']:
        return jsonify({"error": "OTP has expired. Please request a new one."}), 400

    if record['otp'] != otp:
        return jsonify({"error": "Incorrect OTP. Please try again."}), 401

    # OTP verified — create or fetch user
    user = db.users.find_one({"phone": phone, "role": role})
    if not user:
        user_id = phone + "_" + role
        user = {
            "_id": user_id,
            "phone": phone,
            "role": role,
            "name": name,
            "created_at": time.time()
        }
        db.users.insert_one(user)
    
    # Clean up OTP
    db.otp_store.delete_one({"phone": phone, "role": role})

    user['id'] = user.pop('_id')
    return jsonify({
        "message": "Login successful",
        "user": user
    })


@auth_bp.route('/get-user/<phone>/<role>', methods=['GET'])
def get_user(phone, role):
    db = get_db()
    user = db.users.find_one({"phone": phone, "role": role})
    if not user:
        return jsonify({"error": "User not found"}), 404
    user['id'] = str(user.pop('_id'))
    return jsonify(user)

@auth_bp.route('/api/patient/signup', methods=['POST'])
def patient_signup():
    db = get_db()
    data = request.json
    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    if db.users.find_one({"$or": [{"email": data['email']}, {"phone": data['phone']}], "role": "patient"}):
        return jsonify({"error": "Patient with this email or phone already exists"}), 400

    user = {
        "name": data['name'],
        "age": data['age'],
        "blood_group": data['blood_group'],
        "conditions": data.get('conditions', ''),
        "phone": data['phone'],
        "email": data['email'],
        "password": data['password'],
        "role": "patient",
        "created_at": time.time()
    }
    result = db.users.insert_one(user)

    # Also register as a patient in the patients collection for backward compatibility
    patient = {
        "_id": str(result.inserted_id)[:8],
        "name": data['name'],
        "age": data['age'],
        "blood_group": data['blood_group'],
        "conditions": data.get('conditions', ''),
        "phone": data['phone'],
        "lat": 17.3850,
        "lng": 78.4867
    }
    db.patients.insert_one(patient)

    user['id'] = str(result.inserted_id)
    del user['_id']
    del user['password']

    return jsonify({"message": "Signup successful", "user": user}), 201

@auth_bp.route('/api/patient/login', methods=['POST'])
def patient_login():
    db = get_db()
    data = request.json
    identifier = data.get('identifier')
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"error": "Identifier and password required"}), 400

    user = db.users.find_one({
        "$or": [{"email": identifier}, {"phone": identifier}],
        "password": password,
        "role": "patient"
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = str(user.pop('_id'))
    del user['password']
    return jsonify({"message": "Login successful", "user": user})

@auth_bp.route('/api/hospital/login', methods=['POST'])
def hospital_login():
    db = get_db()
    data = request.json
    hospital_name = data.get('hospital_name')
    doctor_id = data.get('doctor_id')
    password = data.get('password')
    hospital_code = data.get('hospital_code')

    if not all([hospital_name, doctor_id, password, hospital_code]):
        return jsonify({"error": "All fields are required"}), 400

    user = db.users.find_one({
        "hospital_name": hospital_name,
        "$or": [{"doctor_id": doctor_id}, {"email": doctor_id}],
        "password": password,
        "hospital_code": hospital_code,
        "role": "hospital"
    })

    # For prototype, if no hospital user exists, we can allow a demo one or create it
    if not user:
        if password == "admin123": # Simple hardcoded password for prototype demo
             user = {
                "hospital_name": hospital_name,
                "doctor_id": doctor_id,
                "hospital_code": hospital_code,
                "role": "hospital",
                "name": doctor_id
             }
             # Do not save to DB, just return as successful login for prototype
             user['id'] = "HOSP_DEMO_ID"
             return jsonify({"message": "Login successful (Demo)", "user": user})
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = str(user.pop('_id'))
    del user['password']
    return jsonify({"message": "Login successful", "user": user})
