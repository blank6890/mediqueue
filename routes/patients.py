from flask import Blueprint, request, jsonify
from db import get_db
import uuid

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/api/patient/signup', methods=['POST'])
def signup_patient():
    body = request.get_json()

    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for field in required:
        if not body.get(field):
            return jsonify({"error": f"Missing or empty field: {field}"}), 400

    db = get_db()
    # Check if user already exists
    if db.patients.find_one({"$or": [{"email": body['email']}, {"phone": body['phone']}]}):
        return jsonify({"error": "Patient with this email or phone already exists"}), 400

    patient_id = "P-" + str(uuid.uuid4())[:8].upper()
    patient = {
        "_id": patient_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('conditions', ''),
        "phone": body['phone'],
        "email": body['email'],
        "password": body['password'], # In a real app, hash this
        "lat": body.get('lat', 17.3850),
        "lng": body.get('lng', 78.4867)
    }

    db.patients.insert_one(patient)

    patient_data = {k: v for k, v in patient.items() if k != 'password'}
    patient_data['id'] = patient_data.pop('_id')

    return jsonify({
        "message": "Patient registered successfully",
        "patient": patient_data
    }), 201

@patients_bp.route('/api/patient/login', methods=['POST'])
def login_patient():
    body = request.get_json()
    identifier = body.get('identifier') # email or phone
    password = body.get('password')

    if not identifier or not password:
        return jsonify({"error": "Identifier and password are required"}), 400

    db = get_db()
    patient = db.patients.find_one({
        "$and": [
            {"$or": [{"email": identifier}, {"phone": identifier}]},
            {"password": password}
        ]
    })

    if not patient:
        return jsonify({"error": "Invalid credentials"}), 401

    patient['id'] = str(patient.pop('_id'))
    if 'password' in patient:
        del patient['password']

    return jsonify({
        "message": "Login successful",
        "user": patient
    })

@patients_bp.route('/register-patient', methods=['POST'])
def register_patient_legacy():
    # Keep legacy for compatibility if needed, but point to new logic or just keep old
    return signup_patient()

@patients_bp.route('/get-patient/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    db = get_db()
    patient = db.patients.find_one({"_id": patient_id})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    patient['id'] = str(patient.pop('_id'))
    if 'password' in patient:
        del patient['password']
    return jsonify(patient)
