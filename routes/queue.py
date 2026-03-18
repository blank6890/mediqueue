from flask import Blueprint, request, jsonify
from db import get_db
import uuid
import qrcode
import io
import base64
from datetime import datetime

queue_bp = Blueprint('queue', __name__)

@queue_bp.route('/book-slot', methods=['POST'])
def book_slot():
    body = request.get_json()

    required = ['patient_id', 'hospital', 'doctor', 'slot_time']
    for field in required:
        if field not in body:
            return jsonify({"error": f"Missing field: {field}"}), 400

    db = get_db()
    patient = db.patients.find_one({"_id": body['patient_id']})
    if not patient:
        return jsonify({"error": "Patient not found. Register first."}), 404

    position = db.queue.count_documents({"status": {"$in": ["booked", "present"]}}) + 1
    booking_id = "MQ-" + str(uuid.uuid4())[:4].upper()
    booking = {
        "_id": booking_id,
        "patient_id": body['patient_id'],
        "patient_name": patient['name'],
        "hospital": body['hospital'],
        "doctor": body['doctor'],
        "slot_time": body['slot_time'],
        "status": "booked",
        "position": position,
        "created_at": datetime.now().isoformat()
    }

    db.queue.insert_one(booking)

    qr_data = f"MediQueue|{booking_id}|{patient['name']}|{body['slot_time']}"
    qr = qrcode.make(qr_data)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return jsonify({
        "message": "Slot booked successfully",
        "booking_id": booking_id,
        "position_in_queue": position,
        "slot_time": body['slot_time'],
        "qr_code": f"data:image/png;base64,{qr_base64}"
    }), 201


@queue_bp.route('/get-queue', methods=['GET'])
def get_queue():
    db = get_db()
    active = list(db.queue.find({"status": {"$in": ["booked", "present", "missed"]}}))
    for item in active:
        item['booking_id'] = item.pop('_id')
    return jsonify({"total_in_queue": len(active), "queue": active})


@queue_bp.route('/update-status', methods=['POST'])
def update_status():
    body = request.get_json()
    booking_id = body.get('booking_id')
    new_status = body.get('status')

    allowed = ['present', 'done', 'missed']
    if new_status not in allowed:
        return jsonify({"error": f"Status must be one of: {allowed}"}), 400

    db = get_db()
    result = db.queue.update_one({"_id": booking_id}, {"$set": {"status": new_status}})

    if result.matched_count == 0:
        return jsonify({"error": "Booking not found"}), 404

    return jsonify({"message": f"Status updated to {new_status}"})
