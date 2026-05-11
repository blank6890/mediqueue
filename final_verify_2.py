from app import app
import json
import uuid

client = app.test_client()

def verify_all():
    unique_id = str(uuid.uuid4())[:8]
    # 1. Test Patient Signup
    p_signup = client.post('/api/patient/signup',
                           data=json.dumps({
                               "name": "Verify Patient", "age": 25, "blood_group": "A+",
                               "phone": f"9999{unique_id}", "email": f"verify_{unique_id}@example.com",
                               "password": "pass", "conditions": "None"
                           }), content_type='application/json')
    print("Patient Signup:", p_signup.status_code)
    print(p_signup.get_json())

    # 2. Test Patient Login
    p_login = client.post('/api/patient/login',
                          data=json.dumps({"identifier": f"verify_{unique_id}@example.com", "password": "pass"}),
                          content_type='application/json')
    print("Patient Login:", p_login.status_code)
    print(p_login.get_json())

if __name__ == "__main__":
    verify_all()
