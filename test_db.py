from db import init_db, get_db
import os

try:
    init_db()
    db = get_db()
    print("Collections:", db.list_collection_names())
except Exception as e:
    print("Error:", e)
