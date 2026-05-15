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
    user['id'] = user.pop('_id')
    return jsonify(user)

@auth_bp.route('/api/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    db = get_db()

    # Check if exists
    if db.patients.find_one({"$or": [{"phone": body.get('phone')}, {"email": body.get('email')}]}):
        return jsonify({"error": "Patient already exists"}), 400

    from routes.patients import register_patient
    # This is a bit hacky because register_patient is a route, but for prototype it works
    # Or we can just re-implement here
    import uuid
    patient_id = "P-" + str(uuid.uuid4())[:6].upper()
    patient = {
        "_id": patient_id,
        "name": body.get('name'),
        "age": body.get('age'),
        "blood_group": body.get('blood_group'),
        "conditions": body.get('conditions'),
        "phone": body.get('phone'),
        "email": body.get('email'),
        "password": body.get('password'),
        "role": "patient"
    }
    db.patients.insert_one(patient)
    patient['id'] = patient.pop('_id')
    return jsonify({"message": "Signup successful", "user": patient})

@auth_bp.route('/api/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    login_id = body.get('loginId') # phone or email
    password = body.get('password')

    db = get_db()
    user = db.patients.find_one({
        "$and": [
            {"$or": [{"phone": login_id}, {"email": login_id}]},
            {"password": password}
        ]
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = str(user.pop('_id'))
    user['role'] = 'patient'
    return jsonify({"message": "Login successful", "user": user})

@auth_bp.route('/api/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    # For prototype, we accept any login but check hospital code against our list
    h_code = body.get('hospitalCode')

    from routes.hospitals import HOSPITALS
    hospital = next((h for h in HOSPITALS if h['id'] == h_code), None)

    if not hospital:
         return jsonify({"error": "Invalid Hospital Code"}), 401

    user = {
        "name": body.get('doctorName') or body.get('hospitalName'),
        "hospitalName": hospital['name'],
        "hospitalCode": h_code,
        "role": "hospital",
        "email": body.get('loginId')
    }
    return jsonify({"message": "Login successful", "user": user})
