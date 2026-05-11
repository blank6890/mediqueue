from app import app
import json

client = app.test_client()

def test_signup():
    payload = {
        "name": "Test Patient",
        "age": 30,
        "blood_group": "O+",
        "phone": "1234567890",
        "email": "test@example.com",
        "password": "password123",
        "conditions": "None"
    }
    response = client.post('/api/patient/signup',
                           data=json.dumps(payload),
                           content_type='application/json')
    print("Signup Status:", response.status_code)
    print("Signup Response:", response.get_json())

def test_login():
    payload = {
        "identifier": "test@example.com",
        "password": "password123"
    }
    response = client.post('/api/patient/login',
                           data=json.dumps(payload),
                           content_type='application/json')
    print("Login Status:", response.status_code)
    print("Login Response:", response.get_json())

if __name__ == "__main__":
    # Note: This might fail if DB is not reachable or env vars are missing
    # But let's try to see if logic is sound.
    try:
        test_signup()
        test_login()
    except Exception as e:
        print("Error during test:", e)
