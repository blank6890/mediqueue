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

# Initialize Twilio only if credentials are provided
twilio = None
if TWILIO_SID and TWILIO_TOKEN:
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

    if twilio:
        try:
            twilio.messages.create(
                body=f"Your MediQueue OTP is: {otp}. Valid for 5 minutes. Do not share this with anyone.",
                from_=TWILIO_PHONE,
                to=phone
            )
            return jsonify({"message": "OTP sent successfully", "phone": phone})
        except Exception as e:
            return jsonify({"error": "Failed to send OTP: " + str(e)}), 500
    else:
        return jsonify({"message": "OTP generated (Twilio not configured)", "otp": otp, "phone": phone})


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

    user['id'] = str(user.pop('_id'))
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

# --- NEW AUTH FLOWS FOR PROTOTYPE ---

@auth_bp.route('/api/patient/signup', methods=['POST'])
def patient_signup():
    data = request.get_json()
    db = get_db()

    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Check if user already exists
    existing = db.users.find_one({"$or": [{"phone": data['phone']}, {"email": data['email']}]})
    if existing:
        return jsonify({"error": "User with this phone or email already exists"}), 400

    user = {
        "name": data['name'],
        "age": data['age'],
        "blood_group": data['blood_group'],
        "conditions": data.get('conditions', ''),
        "phone": data['phone'],
        "email": data['email'],
        "password": data['password'], # Plaintext for prototype
        "role": "patient",
        "created_at": time.time()
    }

    result = db.users.insert_one(user)

    # Also create a patient record for compatibility with existing logic
    patient = {
        "_id": str(result.inserted_id),
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
    user.pop('_id')
    return jsonify({"message": "Signup successful", "user": user}), 201

@auth_bp.route('/api/patient/login', methods=['POST'])
def patient_login():
    data = request.get_json()
    db = get_db()
    identifier = data.get('identifier') # phone or email
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"error": "Identifier and password are required"}), 400

    user = db.users.find_one({
        "$or": [{"phone": identifier}, {"email": identifier}],
        "password": password,
        "role": "patient"
    })

    if user:
        user['id'] = str(user.pop('_id'))
        return jsonify({"message": "Login successful", "user": user})

    return jsonify({"error": "Invalid credentials"}), 401

@auth_bp.route('/api/hospital/login', methods=['POST'])
def hospital_login():
    data = request.get_json()
    # Hospital Name, Doctor ID or Email, Password, Hospital Code
    required = ['hospital_name', 'identifier', 'password', 'hospital_code']
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400

    # Mock auth for hospital
    user = {
        "hospital_name": data['hospital_name'],
        "doctor_identifier": data['identifier'],
        "hospital_code": data['hospital_code'],
        "role": "hospital"
    }

    return jsonify({"message": "Login successful", "user": user})
