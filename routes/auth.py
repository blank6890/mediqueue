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

@auth_bp.route('/api/hospital/login', methods=['POST'])
def login_hospital():
    body = request.get_json()
    hospital_name = body.get('hospital_name')
    identifier = body.get('identifier') # Doctor ID or email
    password = body.get('password')
    hospital_code = body.get('hospital_code')

    if not hospital_name or not identifier or not password or not hospital_code:
        return jsonify({"error": "All fields are required"}), 400

    # For prototype, we validate against a simple mock or just allow if fields are present
    # In real app, we would check a 'hospitals' and 'doctors' collection

    user = {
        "id": identifier,
        "role": "hospital",
        "hospital": hospital_name,
        "hospital_code": hospital_code,
        "name": identifier # or fetch from DB
    }

    return jsonify({
        "message": "Hospital login successful",
        "user": user
    })
