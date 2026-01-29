# 🥗 Diet Planner API

A Django REST API for managing diet plans, user profiles, and nutrition tracking with AI-powered features.

## 🚀 Features

- **User Authentication**: JWT-based authentication with token refresh
- **User Profiles**: Manage user profiles with custom settings
- **AI Integration**: OpenAI integration for intelligent diet recommendations
- **SMS Notifications**: Twilio integration for SMS notifications (optional)
- **API Documentation**: Auto-generated API docs with Swagger/OpenAPI
- **CORS Enabled**: Ready for frontend integration

## 📋 Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/diet-planner.git
cd diet-planner
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Setup

Copy the example environment file and update with your values:

```bash
cp .env.example config/.env
```

Edit `config/.env` and add your actual values:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL_NAME=nvidia/nemotron-3-nano-30b-a3b:free
OPENAI_IMAGE_MODEL_NAME=stabilityai/stable-diffusion-xl-base-1.0
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000`

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

## 🔑 API Endpoints

### Authentication
- `POST /api/accounts/register/` - Register new user
- `POST /api/accounts/login/` - Login and get JWT tokens
- `POST /api/accounts/token/refresh/` - Refresh access token
- `POST /api/accounts/logout/` - Logout (blacklist token)

### User Profile
- `GET /api/accounts/profile/` - Get user profile
- `PUT /api/accounts/profile/` - Update user profile
- `PATCH /api/accounts/profile/` - Partial update profile

## 🐳 Docker Support

### Build and Run with Docker

```bash
docker-compose up --build
```

The API will be available at: `http://localhost:8000`

## 🌐 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to:
- Render
- Railway
- PythonAnywhere
- Other platforms

## 🔒 Security

- Never commit `.env` files to Git
- Use strong `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Configure proper `ALLOWED_HOSTS`
- Use HTTPS in production

## 📦 Project Structure

```
diet-planner/
├── accounts/           # User accounts app
├── config/            # Django settings
│   ├── .env          # Environment variables (not in Git)
│   └── settings.py   # Django settings
├── .gitignore        # Git ignore file
├── .env.example      # Example environment file
├── requirements.txt  # Python dependencies
├── manage.py         # Django management script
├── DEPLOYMENT.md     # Deployment guide
└── README.md         # This file
```

## 🧪 Testing

```bash
python manage.py test
```

## 📝 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Django secret key | Yes | - |
| `DEBUG` | Debug mode | No | `True` |
| `ALLOWED_HOSTS` | Allowed hosts (comma-separated) | No | `*` |
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `OPENAI_BASE_URL` | OpenAI base URL | No | `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL_NAME` | AI model name | No | `nvidia/nemotron-3-nano-30b-a3b:free` |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | No | - |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | No | - |
| `TWILIO_FROM_NUMBER` | Twilio phone number | No | - |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Author

Your Name

## 🙏 Acknowledgments

- Django REST Framework
- OpenAI
- Twilio
- All contributors

---

**Happy Coding! 🚀**
