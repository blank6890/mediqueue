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

try:
    twilio = Client(TWILIO_SID, TWILIO_TOKEN)
except Exception:
    twilio = None

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
        return jsonify({"message": "Twilio not configured. OTP (mock): " + otp, "phone": phone, "otp": otp})


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

@auth_bp.route('/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for field in required:
        if not body.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400

    db = get_db()
    # Check if user already exists
    if db.patients.find_one({"$or": [{"phone": body['phone']}, {"email": body['email']}]}):
        return jsonify({"error": "User with this phone or email already exists"}), 400

    patient_id = "P-" + str(random.randint(100000, 999999))
    patient = {
        "_id": patient_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('conditions', ''),
        "phone": body['phone'],
        "email": body['email'],
        "password": body['password'], # In a real app, hash this!
        "created_at": time.time()
    }
    db.patients.insert_one(patient)

    return jsonify({
        "message": "Patient registered successfully",
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
        return jsonify({"error": "Email/Phone and password are required"}), 400

    db = get_db()
    user = db.patients.find_one({
        "$and": [
            {"$or": [{"phone": user_id}, {"email": user_id}]},
            {"password": password}
        ]
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user['_id'],
            "name": user['name'],
            "role": "patient"
        }
    })

@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    hospital_name = body.get('hospital_name')
    doctor_id = body.get('doctor_id') # or email
    hospital_code = body.get('hospital_code')
    password = body.get('password')

    if not all([hospital_name, doctor_id, hospital_code, password]):
        return jsonify({"error": "All fields are required"}), 400

    # For prototype, we accept any login that matches a code or just mock it
    # Ideally we'd have a 'hospitals' collection with these codes.
    # We'll just return success for the prototype as requested.

    return jsonify({
        "message": "Hospital login successful",
        "user": {
            "hospital": hospital_name,
            "hospitalCode": hospital_code,
            "doctor": doctor_id,
            "role": "hospital"
        }
    })

@auth_bp.route('/get-user/<phone>/<role>', methods=['GET'])
def get_user(phone, role):
    db = get_db()
    user = db.users.find_one({"phone": phone, "role": role})
    if not user:
        return jsonify({"error": "User not found"}), 404
    user['id'] = user.pop('_id')
    return jsonify(user)
