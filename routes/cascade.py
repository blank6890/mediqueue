from flask import Blueprint, request, jsonify
from db import get_db
import math

cascade_bp = Blueprint('cascade', __name__)

def haversine_distance(lat1, lng1, lat2, lng2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_nearest_patients(hospital_lat, hospital_lng, booked_patients, limit=5):
    patients_with_distance = []
    for patient in booked_patients:
        lat = patient.get('lat', 17.3850)
        lng = patient.get('lng', 78.4867)
        distance = haversine_distance(hospital_lat, hospital_lng, lat, lng)
        patients_with_distance.append({
            "patient_id": patient['_id'],
            "patient_name": patient['name'],
            "phone": patient.get('phone', ''),
            "distance_km": round(distance, 2)
        })
    patients_with_distance.sort(key=lambda x: x['distance_km'])
    return patients_with_distance[:limit]

@cascade_bp.route('/trigger-cascade', methods=['POST'])
def trigger_cascade():
    body = request.get_json()
    missed_booking_id = body.get('booking_id')

    if not missed_booking_id:
        return jsonify({"error": "booking_id is required"}), 400

    db = get_db()
    db.queue.update_one({"_id": missed_booking_id}, {"$set": {"status": "missed"}})
    missed = db.queue.find_one({"_id": missed_booking_id})

    if not missed:
        return jsonify({"error": "Booking not found"}), 404

    hospital_lat = body.get('hospital_lat', 17.4317)
    hospital_lng = body.get('hospital_lng', 78.4070)

    booked_queue = list(db.queue.find({"status": "booked"}))
    booked_patient_ids = [b['patient_id'] for b in booked_queue]

    if not booked_patient_ids:
        return jsonify({"message": "No available patients to fill the slot", "cascade": []}), 200

    available_patients = list(db.patients.find({"_id": {"$in": booked_patient_ids}}))
    cascade_order = find_nearest_patients(hospital_lat, hospital_lng, available_patients)

    return jsonify({
        "message": "GPS cascade triggered",
        "missed_slot": missed_booking_id,
        "slot_time": missed.get('slot_time'),
        "cascade_order": cascade_order,
        "action": "Notify patients in this order. First to confirm gets the slot."
    })

@cascade_bp.route('/accept-cascade', methods=['POST'])
def accept_cascade():
    body = request.get_json()
    patient_id = body.get('patient_id')
    missed_booking_id = body.get('missed_booking_id')

    if not patient_id or not missed_booking_id:
        return jsonify({"error": "patient_id and missed_booking_id are required"}), 400

    db = get_db()
    original = db.queue.find_one({"patient_id": patient_id, "status": "booked"})
    if not original:
        return jsonify({"error": "No active booking found for this patient"}), 404

    missed = db.queue.find_one({"_id": missed_booking_id})
    if not missed:
        return jsonify({"error": "Missed booking not found"}), 404

    db.queue.update_one(
        {"_id": original['_id']},
        {"$set": {
            "position": missed['position'],
            "slot_time": missed['slot_time'],
            "status": "present",
            "cascade_accepted": True
        }}
    )

    return jsonify({
        "message": "Slot accepted! Patient moved up in queue.",
        "patient": patient_id,
        "new_slot_time": missed['slot_time'],
        "new_position": missed['position']
    })
