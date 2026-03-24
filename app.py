from flask import Flask, render_template
from flask_cors import CORS
from routes.patients import patients_bp
from routes.queue import queue_bp
from routes.cascade import cascade_bp
from routes.hospitals import hospitals_bp
from routes.auth import auth_bp
from db import init_db

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

init_db()

app.register_blueprint(patients_bp)
app.register_blueprint(queue_bp)
app.register_blueprint(cascade_bp)
app.register_blueprint(hospitals_bp)
app.register_blueprint(auth_bp)

@app.route('/')
@app.route('/patient/login')
@app.route('/patient/signup')
@app.route('/hospital/login')
def home():
    return render_template('index.html')

@app.route('/api')
def api_status():
    return {
        "message": "MediQueue API is running!",
        "status": "ok",
        "database": "MongoDB Atlas"
    }

if __name__ == '__main__':
    app.run(debug=False)
