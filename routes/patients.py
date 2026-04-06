from flask import Blueprint, request, jsonify
from db import get_db
import uuid

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/register-patient', methods=['POST'])
def register_patient():
    body = request.get_json()

    required = ['name', 'age', 'blood_group', 'phone', 'email', 'password']
    for field in required:
        if field not in body:
            return jsonify({"error": f"Missing field: {field}"}), 400

    db = get_db()

    # Check if patient already exists
    existing = db.patients.find_one({"$or": [{"phone": body['phone']}, {"email": body['email']}]})
    if existing:
        return jsonify({"error": "Patient with this phone or email already exists"}), 400

    patient_id = str(uuid.uuid4())[:8]
    patient = {
        "_id": patient_id,
        "name": body['name'],
        "age": body['age'],
        "blood_group": body['blood_group'],
        "conditions": body.get('conditions', ''),
        "phone": body['phone'],
        "email": body['email'],
        "password": body['password'], # In a real app, we would hash this
        "lat": body.get('lat', 17.3850),
        "lng": body.get('lng', 78.4867)
    }

    db.patients.insert_one(patient)

    return jsonify({
        "message": "Patient registered successfully",
        "patient_id": patient_id,
        "patient": {k: v for k, v in patient.items() if k != '_id' and k != 'password'}
    }), 201


@patients_bp.route('/get-patient/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    db = get_db()
    patient = db.patients.find_one({"_id": patient_id})
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    patient['id'] = patient.pop('_id')
    if 'password' in patient:
        del patient['password']
    return jsonify(patient)
