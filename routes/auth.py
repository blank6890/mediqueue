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


@auth_bp.route('/get-user/<phone>/<role>', methods=['GET'])
def get_user(phone, role):
    db = get_db()
    user = db.users.find_one({"phone": phone, "role": role})
    if not user:
        return jsonify({"error": "User not found"}), 404
    user['id'] = user.pop('_id')
    return jsonify(user)

# --- NEW AUTH ENDPOINTS FOR PROTOTYPE ---

@auth_bp.route('/patient/signup', methods=['POST'])
def patient_signup():
    db = get_db()
    data = request.get_json()

    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for f in required:
        if not data.get(f):
            return jsonify({"error": f"Missing field: {f}"}), 400

    # Check if user already exists
    if db.users.find_one({"$or": [{"phone": data['phone']}, {"email": data['email']}], "role": "patient"}):
        return jsonify({"error": "User with this phone or email already exists"}), 400

    user_id = "P-" + str(random.randint(10000, 99999))
    user = {
        "_id": user_id,
        "role": "patient",
        "name": data['name'],
        "age": data['age'],
        "blood_group": data['blood_group'],
        "conditions": data.get('conditions', ''),
        "phone": data['phone'],
        "email": data['email'],
        "password": data['password'], # Plaintext for prototype
        "created_at": time.time()
    }
    db.users.insert_one(user)

    # Also sync to patients collection for compatibility with existing code
    patient = {
        "_id": user_id,
        "name": data['name'],
        "age": data['age'],
        "blood_group": data['blood_group'],
        "conditions": data.get('conditions', ''),
        "phone": data['phone'],
        "lat": 17.3850,
        "lng": 78.4867
    }
    db.patients.insert_one(patient)

    user['id'] = user.pop('_id')
    return jsonify({"message": "Signup successful", "user": user}), 201

@auth_bp.route('/patient/login', methods=['POST'])
def patient_login():
    db = get_db()
    data = request.get_json()

    user_id_or_email = data.get('user')
    password = data.get('password')

    if not user_id_or_email or not password:
        return jsonify({"error": "Credentials required"}), 400

    user = db.users.find_one({
        "$or": [{"phone": user_id_or_email}, {"email": user_id_or_email}],
        "password": password,
        "role": "patient"
    })

    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    user['id'] = user.pop('_id')
    return jsonify({"message": "Login successful", "user": user})

@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    db = get_db()
    data = request.get_json()

    hospital_name = data.get('hospital_name')
    user_id_or_email = data.get('user')
    hospital_code = data.get('hospital_code')
    password = data.get('password')

    if not all([hospital_name, user_id_or_email, hospital_code, password]):
        return jsonify({"error": "All fields required"}), 400

    # In a real app, we'd verify hospital_code and doctor credentials.
    # For prototype, we'll just check if a user exists or create one if it's a first-time mock login.
    user = db.users.find_one({
        "role": "hospital",
        "hospital_code": hospital_code,
        "hospital_name": hospital_name,
        "$or": [{"phone": user_id_or_email}, {"email": user_id_or_email}],
        "password": password
    })

    if not user:
        # For prototype convenience, if it's the first time, we could "auto-register" or just return 401.
        # Let's just mock it: if password is 'admin', let them in and save.
        if password == 'admin' or password == 'password':
            user_id = "H-" + str(random.randint(10000, 99999))
            user = {
                "_id": user_id,
                "role": "hospital",
                "hospital_name": hospital_name,
                "hospital_code": hospital_code,
                "email": user_id_or_email if "@" in user_id_or_email else "",
                "phone": user_id_or_email if "@" not in user_id_or_email else "",
                "password": password,
                "created_at": time.time()
            }
            db.users.insert_one(user)
        else:
            return jsonify({"error": "Invalid hospital credentials"}), 401

    user['id'] = user.pop('_id')
    return jsonify({"message": "Login successful", "user": user})
