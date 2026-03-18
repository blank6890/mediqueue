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

def get_db():
    return db