from flask import Blueprint, jsonify

hospitals_bp = Blueprint('hospitals', __name__)

HOSPITALS = [
  {
    "id": "HOSP-001",
    "name": "Apollo Clinic — Jubilee Hills",
    "location": { "lat": 17.4326, "lng": 78.4071 },
    "city": "Hyderabad",
    "departments": ["General OPD", "Cardiology", "Orthopaedics", "Dermatology"],
    "doctors": ["Dr. Ramesh Kumar", "Dr. Priya Nair"],
    "availableSlots": ["09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
                     "11:00 AM", "11:30 AM", "02:00 PM", "02:30 PM"]
  },
  {
    "id": "HOSP-002",
    "name": "Yashoda Hospital — Secunderabad",
    "location": { "lat": 17.4399, "lng": 78.4983 },
    "city": "Hyderabad",
    "departments": ["General OPD", "Neurology", "Paediatrics", "ENT"],
    "doctors": ["Dr. Suresh Reddy", "Dr. Anitha Sharma"],
    "availableSlots": ["09:00 AM", "10:00 AM", "11:00 AM",
                     "12:00 PM", "03:00 PM", "04:00 PM"]
  },
  {
    "id": "HOSP-003",
    "name": "NIMS Polyclinic — Punjagutta",
    "location": { "lat": 17.4274, "lng": 78.4601 },
    "city": "Hyderabad",
    "departments": ["General OPD", "Gynaecology", "Ophthalmology"],
    "doctors": ["Dr. Kavitha Rao", "Dr. Arjun Mehta"],
    "availableSlots": ["08:30 AM", "09:00 AM", "09:30 AM",
                     "10:00 AM", "02:00 PM", "03:00 PM"]
  },
  {
    "id": "HOSP-004",
    "name": "Care Hospital — Banjara Hills",
    "location": { "lat": 17.4156, "lng": 78.4347 },
    "city": "Hyderabad",
    "departments": ["General OPD", "Cardiology", "Oncology", "Urology"],
    "doctors": ["Dr. Srinivas Goud", "Dr. Meena Iyer"],
    "availableSlots": ["10:00 AM", "10:30 AM", "11:00 AM",
                     "11:30 AM", "04:00 PM", "04:30 PM"]
  },
  {
    "id": "HOSP-005",
    "name": "Sunshine Hospital — Gachibowli",
    "location": { "lat": 17.4400, "lng": 78.3489 },
    "city": "Hyderabad",
    "departments": ["General OPD", "Orthopaedics", "Physiotherapy"],
    "doctors": ["Dr. Ravi Teja", "Dr. Pooja Desai"],
    "availableSlots": ["09:00 AM", "09:30 AM", "11:00 AM",
                     "11:30 AM", "03:30 PM", "04:00 PM"]
  },
  {
    "id": "HOSP-006",
    "name": "Medicover Hospital — HITEC City",
    "location": { "lat": 17.4473, "lng": 78.3762 },
    "city": "Hyderabad",
    "departments": ["General OPD", "Dermatology", "Psychiatry", "Endocrinology"],
    "doctors": ["Dr. Lakshmi Prasad", "Dr. Arun Nambiar"],
    "availableSlots": ["08:00 AM", "08:30 AM", "09:00 AM",
                     "02:00 PM", "02:30 PM", "05:00 PM"]
  },
  {
    "id": "HOSP-007",
    "name": "Rainbow Children's Hospital — Banjara Hills",
    "location": { "lat": 17.4231, "lng": 78.4508 },
    "city": "Hyderabad",
    "departments": ["Paediatrics", "Neonatology", "Paediatric Surgery"],
    "doctors": ["Dr. Vandana Reddy", "Dr. Kiran Babu"],
    "availableSlots": ["09:00 AM", "10:00 AM", "11:00 AM", "03:00 PM", "04:00 PM"]
  },
  {
    "id": "HOSP-008",
    "name": "Gleneagles Global Hospital — LB Nagar",
    "location": { "lat": 17.3616, "lng": 78.5541 },
    "city": "Hyderabad",
    "departments": ["General OPD", "Nephrology", "Transplant", "Gastroenterology"],
    "doctors": ["Dr. Harish Chandra", "Dr. Deepa Srinivasan"],
    "availableSlots": ["10:00 AM", "10:30 AM", "11:30 AM",
                     "12:00 PM", "03:00 PM", "03:30 PM"]
  }
]

@hospitals_bp.route('/get-hospitals', methods=['GET'])
def get_hospitals():
    return jsonify(HOSPITALS)
