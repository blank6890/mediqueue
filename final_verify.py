from app import app
import json

client = app.test_client()

def verify_all():
    # 1. Test Patient Signup
    p_signup = client.post('/api/patient/signup',
                           data=json.dumps({
                               "name": "Verify Patient", "age": 25, "blood_group": "A+",
                               "phone": "9999999999", "email": "verify@example.com",
                               "password": "pass", "conditions": "None"
                           }), content_type='application/json')
    print("Patient Signup:", p_signup.status_code)

    # 2. Test Patient Login
    p_login = client.post('/api/patient/login',
                          data=json.dumps({"identifier": "verify@example.com", "password": "pass"}),
                          content_type='application/json')
    print("Patient Login:", p_login.status_code)

    # 3. Test Hospital Login
    h_login = client.post('/api/hospital/login',
                          data=json.dumps({
                              "hospital_name": "Test Hospital", "identifier": "DOC-1",
                              "password": "pass", "hospital_code": "HOSP-001"
                          }), content_type='application/json')
    print("Hospital Login:", h_login.status_code)

    # 4. Test Queue Serialization
    queue = client.get('/get-queue')
    print("Get Queue:", queue.status_code)
    if queue.status_code == 200:
        data = queue.get_json()
        if data['queue']:
            print("First booking ID type:", type(data['queue'][0]['booking_id']))

if __name__ == "__main__":
    verify_all()
