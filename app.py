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

# Register blueprints with /api prefix for clarity if needed,
# but existing code doesn't use it consistently.
# Let's keep it consistent with what's there or standardize.
# The index.html uses API = ""; so no prefix is expected by frontend yet.
app.register_blueprint(patients_bp, url_prefix='/api')
app.register_blueprint(queue_bp, url_prefix='/api')
app.register_blueprint(cascade_bp, url_prefix='/api')
app.register_blueprint(hospitals_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api')

@app.route('/')
@app.route('/patient/login')
@app.route('/patient/signup')
@app.route('/hospital/login')
@app.route('/patient/dashboard')
@app.route('/hospital/dashboard')
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
    app.run(debug=False, port=5000)
