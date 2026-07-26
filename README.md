# MediQueue

A modern queue management system designed to streamline patient scheduling and hospital operations. MediQueue provides a seamless platform for patients to book appointments and for hospitals to manage their queues efficiently.

## 🎯 Features

- **Patient Portal**: Easy-to-use interface for patients to register, log in, and view their appointments
- **Hospital Dashboard**: Comprehensive queue management system for hospital administrators
- **Queue Management**: Real-time queue tracking and patient flow optimization
- **Authentication**: Secure login system for both patients and hospitals
- **API-First Architecture**: RESTful API endpoints for all operations
- **CORS Support**: Cross-origin resource sharing enabled for flexible frontend integration
- **QR Code Generation**: Built-in QR code functionality for patient identification
- **Database Support**: MongoDB Atlas integration for scalable data storage

## 📋 Project Structure

```
mediqueue/
├── app.py              # Main Flask application
├── db.py               # Database initialization and configuration
├── requirements.txt    # Python dependencies
├── Procfile           # Deployment configuration
├── routes/            # API route handlers
│   ├── patients.py    # Patient-related endpoints
│   ├── queue.py       # Queue management endpoints
│   ├── cascade.py     # Cascade operation handlers
│   ├── hospitals.py   # Hospital-related endpoints
│   └── auth.py        # Authentication endpoints
└── templates/         # HTML templates
    └── index.html     # Main frontend template
```

## 🛠️ Tech Stack

**Backend:**
- Python 3
- Flask - Lightweight web framework
- Flask-CORS - Cross-Origin Resource Sharing support
- PyMongo - MongoDB driver for Python

**Frontend:**
- HTML5
- JavaScript

**Database:**
- MongoDB Atlas - Cloud-based NoSQL database

**Utilities:**
- QRCode - QR code generation
- Pillow - Image processing
- Gunicorn - WSGI HTTP Server
- Certifi - SSL certificates

## 📦 Installation

### Prerequisites
- Python 3.7 or higher
- MongoDB Atlas account
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/blank6890/mediqueue.git
   cd mediqueue
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory with:
   ```
   MONGODB_URI=your_mongodb_atlas_connection_string
   FLASK_ENV=development
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5000`

## 🚀 API Endpoints

All API endpoints are prefixed with `/api`

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/signup` - User registration

### Patients
- `GET /api/patients` - Get patient list
- `POST /api/patients` - Create new patient
- `GET /api/patients/<id>` - Get patient details
- `PUT /api/patients/<id>` - Update patient information

### Queue Management
- `GET /api/queue` - View current queue
- `POST /api/queue` - Add patient to queue
- `PUT /api/queue/<id>` - Update queue status
- `DELETE /api/queue/<id>` - Remove from queue

### Hospitals
- `GET /api/hospitals` - Get hospital list
- `GET /api/hospitals/<id>` - Get hospital details
- `POST /api/hospitals` - Register new hospital

### System
- `GET /api/status` - Check API status

## 🌐 Routes

### Patient Routes
- `/` - Home page
- `/patient/login` - Patient login page
- `/patient/signup` - Patient registration page
- `/patient/dashboard` - Patient dashboard

### Hospital Routes
- `/hospital/login` - Hospital login page
- `/hospital/dashboard` - Hospital dashboard

## 🔒 Security

- CORS enabled with flexible origin policy
- Secure authentication system for patients and hospitals
- MongoDB Atlas connection with SSL/TLS encryption
- Input validation on API endpoints

## 📝 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB Atlas connection string | Yes |
| `FLASK_ENV` | Flask environment (development/production) | Yes |

## 🚢 Deployment

### Using Gunicorn (Recommended for Production)
```bash
gunicorn app:app
```

### Using Heroku (with Procfile)
```bash
git push heroku main
```

## 📊 Database Schema

The application uses MongoDB Atlas. Key collections include:
- `patients` - Patient information and credentials
- `hospitals` - Hospital data and contact details
- `queue` - Patient queue records
- `appointments` - Scheduled appointments

## 🐛 Issue Tracking

The project currently has 53 open issues. Issues can be found in the [GitHub Issues](https://github.com/blank6890/mediqueue/issues) section.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**blank6890**
- GitHub: [@blank6890](https://github.com/blank6890)

## 📞 Support

For support, please open an issue on the [GitHub Issues](https://github.com/blank6890/mediqueue/issues) page.

---

**Made with ❤️ for better healthcare queue management**
