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


@auth_bp.route('/api/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for f in required:
        if f not in body:
            return jsonify({"error": f"Missing field: {f}"}), 400

    db = get_db()
    if db.users.find_one({"$or": [{"email": body['email']}, {"phone": body['phone']}], "role": "patient"}):
        return jsonify({"error": "Patient already exists with this email or phone"}), 400

    user_id = str(random.randint(1000, 9999))
    user = {
        "_id": "P-" + user_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('chronic_conditions', ''),
        "phone": body['phone'],
        "email": body['email'],
        "password": body['password'], # In prototype, we use plain text
        "role": "patient",
        "created_at": time.time()
    }
    db.users.insert_one(user)

    # Also create a patient record for the booking system compatibility
    db.patients.insert_one({
        "_id": "P-" + user_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('chronic_conditions', ''),
        "phone": body['phone']
    })

    user['id'] = user.pop('_id')
    user.pop('password')
    return jsonify({"message": "Signup successful", "user": user}), 201

@auth_bp.route('/api/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    user_id = body.get('username') # email or phone
    password = body.get('password')

    if not user_id or not password:
        return jsonify({"error": "Username and password required"}), 400

    db = get_db()
    user = db.users.find_one({
        "$or": [{"email": user_id}, {"phone": user_id}],
        "role": "patient"
    })

    if not user or user['password'] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = user.pop('_id')
    user.pop('password')
    return jsonify({"message": "Login successful", "user": user})

@auth_bp.route('/api/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    h_name = body.get('hospital_name')
    u_id = body.get('username') # doctor id or email
    h_code = body.get('hospital_code')
    password = body.get('password')

    if not all([h_name, u_id, h_code, password]):
        return jsonify({"error": "All fields are required"}), 400

    # Prototype: allow any login for hospital if it matches a basic rule or just accept it
    # But let's try to find if user exists or just mock it as requested
    db = get_db()
    user = db.users.find_one({"email": u_id, "role": "hospital"})

    if not user:
        # For prototype, if not exists, we can "auto-create" or just validate
        # Let's just validate against a dummy check if not in DB
        user = {
            "id": u_id,
            "name": h_name,
            "hospital": h_name,
            "hospital_code": h_code,
            "role": "hospital"
        }
    else:
        if user['password'] != password:
            return jsonify({"error": "Invalid credentials"}), 401
        user['id'] = user.pop('_id')
        user.pop('password')

    return jsonify({"message": "Hospital login successful", "user": user})

@auth_bp.route('/get-user/<phone>/<role>', methods=['GET'])
def get_user(phone, role):
    db = get_db()
    user = db.users.find_one({"phone": phone, "role": role})
    if not user:
        return jsonify({"error": "User not found"}), 404
    user['id'] = str(user.pop('_id'))
    return jsonify(user)
