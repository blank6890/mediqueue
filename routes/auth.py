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
except:
    twilio = None

def generate_otp():
    return str(random.randint(100000, 999999))

@auth_bp.route('/patient/signup', methods=['POST'])
def patient_signup():
    body = request.get_json()
    name = body.get('name')
    age = body.get('age')
    blood_group = body.get('blood_group')
    conditions = body.get('conditions', '')
    phone = body.get('phone')
    email = body.get('email')
    password = body.get('password')

    if not all([name, age, blood_group, phone, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    db = get_db()
    if db.users.find_one({"$or": [{"phone": phone}, {"email": email}]}):
        return jsonify({"error": "User already exists"}), 400

    user_id = str(phone) + "_patient"
    user = {
        "_id": user_id,
        "phone": phone,
        "email": email,
        "password": password, # In production, hash this!
        "role": "patient",
        "name": name,
        "created_at": time.time()
    }
    db.users.insert_one(user)

    patient = {
        "_id": user_id,
        "name": name,
        "age": age,
        "blood_group": blood_group,
        "conditions": conditions,
        "phone": phone,
        "email": email,
        "lat": 17.3850,
        "lng": 78.4867
    }
    db.patients.insert_one(patient)

    return jsonify({"message": "Signup successful", "user": {"id": user_id, "name": name, "role": "patient"}})

@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    body = request.get_json()
    user_id_input = body.get('user_id') # email or phone
    password = body.get('password')

    if not user_id_input or not password:
        return jsonify({"error": "Missing credentials"}), 400

    db = get_db()
    user = db.users.find_one({
        "$and": [
            {"$or": [{"phone": user_id_input}, {"email": user_id_input}]},
            {"role": "patient"}
        ]
    })

    if not user or user.get('password') != password:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "user": {"id": str(user['_id']), "name": user['name'], "role": "patient"}
    })

@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    body = request.get_json()
    hospital_name = body.get('hospital_name')
    doctor_id = body.get('doctor_id') # or email
    hospital_code = body.get('hospital_code')
    password = body.get('password')

    if not all([hospital_name, doctor_id, hospital_code, password]):
        return jsonify({"error": "Missing credentials"}), 400

    # For prototype, we'll allow any login but store it if it's new
    db = get_db()
    user = db.users.find_one({"doctor_id": doctor_id, "role": "hospital"})

    if not user:
        user = {
            "_id": doctor_id + "_hospital",
            "doctor_id": doctor_id,
            "hospital_name": hospital_name,
            "hospital_code": hospital_code,
            "password": password,
            "role": "hospital",
            "name": doctor_id,
            "created_at": time.time()
        }
        db.users.insert_one(user)
    elif user.get('password') != password:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "user": {"id": str(user['_id']), "name": doctor_id, "role": "hospital", "hospital": hospital_name, "hospitalCode": hospital_code}
    })

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

    if twilio:
        try:
            twilio.messages.create(
                body=f"Your MediQueue OTP is: {otp}",
                from_=TWILIO_PHONE,
                to=phone
            )
            return jsonify({"message": "OTP sent successfully"})
        except:
            return jsonify({"error": "Failed to send OTP"}), 500
    return jsonify({"message": "OTP generated (Twilio not configured)", "otp": otp})

@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    body = request.get_json()
    phone = body.get('phone')
    otp = body.get('otp')
    role = body.get('role')

    db = get_db()
    record = db.otp_store.find_one({"phone": phone, "role": role})

    if not record or record['otp'] != otp:
        return jsonify({"error": "Invalid OTP"}), 401

    user = db.users.find_one({"phone": phone, "role": role})
    if not user:
        user_id = phone + "_" + role
        user = {"_id": user_id, "phone": phone, "role": role, "created_at": time.time()}
        db.users.insert_one(user)
    
    return jsonify({"message": "Login successful", "user": {"id": str(user['_id']), "role": role}})
