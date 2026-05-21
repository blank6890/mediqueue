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

@auth_bp.route('/patient/signup', methods=['POST'])
def patient_signup():
    data = request.get_json()
    db = get_db()

    # Check if patient already exists
    if db.users.find_one({"$or": [{"email": data.get('email')}, {"phone": data.get('phone')}], "role": "patient"}):
        return jsonify({"error": "Patient with this email or phone already exists"}), 400

    user_id = str(random.randint(100000, 999999))
    patient = {
        "_id": user_id,
        "name": data.get('name'),
        "age": data.get('age'),
        "blood_group": data.get('blood_group'),
        "conditions": data.get('conditions'),
        "phone": data.get('phone'),
        "email": data.get('email'),
        "password": data.get('password'),
        "role": "patient",
        "created_at": time.time()
    }

    db.users.insert_one(patient)

    # Also insert into patients collection for compatibility with existing code
    db.patients.insert_one({
        "_id": user_id,
        "name": data.get('name'),
        "age": data.get('age'),
        "blood_group": data.get('blood_group'),
        "conditions": data.get('conditions'),
        "phone": data.get('phone'),
        "lat": 17.3850, # Default Hyderabad
        "lng": 78.4867
    })

    return jsonify({"message": "Signup successful", "user": {"id": user_id, "name": patient['name'], "role": "patient"}})

@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    data = request.get_json()
    identifier = data.get('identifier') # Phone or Email
    password = data.get('password')

    db = get_db()
    user = db.users.find_one({
        "$or": [{"email": identifier}, {"phone": identifier}],
        "password": password,
        "role": "patient"
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "user": {"id": str(user['_id']), "name": user['name'], "role": "patient", "phone": user['phone']}
    })

@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    data = request.get_json()
    hospital_name = data.get('hospital_name')
    identifier = data.get('identifier') # Doctor ID or Email
    hospital_code = data.get('hospital_code')
    password = data.get('password')

    db = get_db()
    # In a real app, we'd verify hospital_code and doctor credentials properly.
    # For prototype, we'll just check if a hospital user exists or create a mock one.
    user = db.users.find_one({
        "$or": [{"email": identifier}, {"doctor_id": identifier}],
        "password": password,
        "role": "hospital",
        "hospital_code": hospital_code
    })

    if not user:
        # For prototype ease, let's allow any login for hospital if it matches a hardcoded password or just accept it
        # Actually, let's be slightly more robust.
        if password == "admin123": # Mock password for demo
            user_id = "H-" + hospital_code
            return jsonify({
                "message": "Login successful",
                "user": {"id": user_id, "name": identifier, "role": "hospital", "hospital": hospital_name, "hospitalCode": hospital_code}
            })
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({
        "message": "Login successful",
        "user": {"id": str(user['_id']), "name": user['name'], "role": "hospital", "hospital": user['hospital'], "hospitalCode": user['hospital_code']}
    })
