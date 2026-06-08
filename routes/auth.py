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

@auth_bp.route('/api/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    name = body.get('name')
    age = body.get('age')
    blood_group = body.get('blood_group')
    conditions = body.get('conditions')
    phone = body.get('phone')
    email = body.get('email')
    password = body.get('password')

    if not all([name, age, blood_group, phone, email, password]):
        return jsonify({"error": "All fields are required"}), 400

    db = get_db()
    if db.users.find_one({"$or": [{"phone": phone}, {"email": email}], "role": "patient"}):
        return jsonify({"error": "User already exists"}), 400

    user_id = str(phone) + "_patient"
    user = {
        "_id": user_id,
        "name": name,
        "age": age,
        "blood_group": blood_group,
        "conditions": conditions,
        "phone": phone,
        "email": email,
        "password": password,
        "role": "patient",
        "created_at": time.time()
    }
    db.users.insert_one(user)

    # Also add to patients collection for compatibility with other routes
    patient = {
        "_id": user_id,
        "name": name,
        "age": int(age),
        "blood_group": blood_group,
        "conditions": conditions or '',
        "phone": phone,
        "lat": 17.3850, "lng": 78.4867
    }
    db.patients.update_one({"_id": user_id}, {"$set": patient}, upsert=True)

    user['id'] = str(user.pop('_id'))
    if 'password' in user: del user['password']
    return jsonify({"message": "Signup successful", "user": user}), 201

@auth_bp.route('/api/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    username = body.get('username')
    password = body.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    db = get_db()
    user = db.users.find_one({
        "$or": [{"phone": username}, {"email": username}],
        "password": password,
        "role": "patient"
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = str(user.pop('_id'))
    if 'password' in user: del user['password']
    return jsonify({"message": "Login successful", "user": user})

@auth_bp.route('/api/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    hospital_name = body.get('hospital_name')
    doctor_user = body.get('doctor_user')
    hospital_code = body.get('hospital_code')
    password = body.get('password')

    if not all([hospital_name, doctor_user, hospital_code, password]):
        return jsonify({"error": "All fields are required"}), 400

    db = get_db()
    user = db.users.find_one({
        "doctor_user": doctor_user,
        "password": password,
        "role": "hospital",
        "hospital_code": hospital_code
    })

    if not user:
        user_id = doctor_user + "_hospital"
        db.users.update_one(
            {"_id": user_id},
            {"$set": {
                "name": doctor_user,
                "hospital": hospital_name,
                "hospital_code": hospital_code,
                "password": password,
                "role": "hospital"
            }},
            upsert=True
        )
        user = db.users.find_one({"_id": user_id})

    user['id'] = str(user.pop('_id'))
    if 'password' in user: del user['password']
    return jsonify({"message": "Hospital login successful", "user": user})

# Restore original Twilio endpoints
@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    body = request.get_json()
    phone = body.get('phone')
    role = body.get('role')

    if not phone or not role:
        return jsonify({"error": "phone and role are required"}), 400

    otp = generate_otp()
    expires_at = time.time() + 300
    db = get_db()
    db.otp_store.update_one(
        {"phone": phone},
        {"$set": {"phone": phone, "otp": otp, "role": role, "expires_at": expires_at}},
        upsert=True
    )

    if not twilio:
        return jsonify({"message": "OTP generated (but Twilio not configured)", "otp": otp})

    try:
        twilio.messages.create(
            body=f"Your MediQueue OTP is: {otp}",
            from_=TWILIO_PHONE, to=phone
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
    db = get_db()
    record = db.otp_store.find_one({"phone": phone, "role": role})
    if not record or time.time() > record['expires_at'] or record['otp'] != otp:
        return jsonify({"error": "Invalid or expired OTP"}), 401

    user = db.users.find_one({"phone": phone, "role": role})
    if not user:
        user_id = phone + "_" + role
        user = {"_id": user_id, "phone": phone, "role": role, "created_at": time.time()}
        db.users.insert_one(user)
    db.otp_store.delete_one({"phone": phone, "role": role})
    user['id'] = str(user.pop('_id'))
    return jsonify({"message": "Login successful", "user": user})

@auth_bp.route('/get-user/<phone>/<role>', methods=['GET'])
def get_user(phone, role):
    db = get_db()
    user = db.users.find_one({"phone": phone, "role": role})
    if not user: return jsonify({"error": "User not found"}), 404
    user['id'] = str(user.pop('_id'))
    return jsonify(user)
