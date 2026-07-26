from pymongo import MongoClient
from urllib.parse import quote_plus
import os
import certifi

username = "mediqueue-admin"
password = quote_plus(os.environ.get("MONGO_PASSWORD", "Mediqueue@123"))
cluster = "cluster0.bxatiz8.mongodb.net"

MONGO_URI = f"mongodb+srv://{username}:{password}@{cluster}/?appName=Cluster0&tlsCAFile={certifi.where()}"

client = None
db = None

def init_db():
    global client, db
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client["mediqueue"]
    print("Connected to MongoDB Atlas successfully!")

    # Seed demo patient MQ-2847
    try:
        if not db.users.find_one({"_id": "MQ-2847"}):
            db.users.insert_one({
                "_id": "MQ-2847",
                "phone": "9876543210",
                "email": "ravi@example.com",
                "password": "password",
                "role": "patient",
                "name": "Ravi Kumar",
                "created_at": 1710000000.0
            })
        if not db.patients.find_one({"_id": "MQ-2847"}):
            db.patients.insert_one({
                "_id": "MQ-2847",
                "name": "Ravi Kumar",
                "age": "35",
                "blood_group": "O+",
                "conditions": "None",
                "phone": "9876543210",
                "email": "ravi@example.com",
                "lat": 17.3850,
                "lng": 78.4867
            })
        print("Demo patient MQ-2847 seeded / verified.")
    except Exception as e:
        print("Seeding error:", e)

def get_db():
    return db