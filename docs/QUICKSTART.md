# 🚀 Quick Start Guide - AI Voice Detection API

## Prerequisites

- Python 3.10+
- FFmpeg (for audio processing)
- Docker (optional, for containerized deployment)

---

## 🏃 Quick Start (Development)

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Server

```bash
# Run the development server
python -m uvicorn app_main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Or using PowerShell:
Invoke-RestMethod -Uri http://localhost:8000/health
```

### 4. View API Documentation

Open your browser and navigate to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📡 API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | No | API information |
| `/health` | GET | No | Health check |
| `/detect` | POST | **Yes** | Voice detection |
| `/docs` | GET | No | Swagger documentation |
| `/metrics` | GET | No | Prometheus metrics |

---

## 🔑 Authentication

All `/detect` requests require an API key in the `X-API-Key` header.

**Default Demo Key**: `demo_key_12345`

### Example Request

```bash
curl -X POST "http://localhost:8000/detect" \
  -H "X-API-Key: demo_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_base64": "<your_base64_audio>",
    "language": "english"
  }'
```

### Python Example

```python
import requests
import base64

# Read and encode audio file
with open("sample.mp3", "rb") as f:
    audio_base64 = base64.b64encode(f.read()).decode()

# Make detection request
response = requests.post(
    "http://localhost:8000/detect",
    headers={"X-API-Key": "demo_key_12345"},
    json={
        "audio_base64": audio_base64,
        "language": "english"
    }
)

result = response.json()
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']:.1%}")
```

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build Docker image
docker build -t voice-detection-api .

# Run container
docker run -d -p 8000:8000 --name voice-api voice-detection-api
```

### Docker Compose (Full Stack)

```bash
# Start all services (API, Redis, PostgreSQL, Nginx, Prometheus)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

---

## 🌍 Supported Languages

| Language | Code |
|----------|------|
| Tamil | `tamil` |
| English | `english` |
| Hindi | `hindi` |
| Malayalam | `malayalam` |
| Telugu | `telugu` |

---

## 📊 Response Format

```json
{
  "prediction": "AI_GENERATED",
  "confidence": 0.923,
  "language": "english",
  "processing_time_ms": 1234.56,
  "timestamp": "2024-02-06T10:30:00Z",
  "audio_duration_seconds": 5.2,
  "model_version": "1.0.0"
}
```

---

## ⚠️ Rate Limits

- **60 requests** per minute
- **1000 requests** per hour

---

## 🧪 Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## 📁 Project Structure

```
files/
├── app/                    # Application package
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic models
│   ├── audio_processor.py # Audio feature extraction
│   ├── classifier.py      # ML classifier
│   └── auth.py           # Authentication
├── app_main.py            # FastAPI application (enhanced)
├── main.py               # Original FastAPI application
├── train_model.py        # Model training script
├── test_api.py           # API test client
├── tests/                # Unit tests
├── models/               # Trained ML models
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Multi-service configuration
├── nginx.conf           # Nginx configuration
├── init.sql             # Database schema
├── prometheus.yml       # Prometheus config
├── .env.example         # Environment template
└── README.md            # Full documentation
```

---

## 🔧 Configuration

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key settings:
- `API_KEYS` - Comma-separated valid API keys
- `LOG_LEVEL` - Logging verbosity
- `RATE_LIMIT_PER_MINUTE` - Rate limiting
- `MODEL_PATH` - Path to trained models

---

## 🚀 Production Checklist

- [ ] Generate secure API keys
- [ ] Configure SSL/TLS
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure database backups
- [ ] Enable error tracking (Sentry)
- [ ] Set appropriate rate limits
- [ ] Train production models

---

## 📞 Support

- **API Docs**: http://localhost:8000/docs
- **Technical Guide**: See `docs/TECHNICAL_GUIDE.md`
- **Business Plan**: See `docs/BUSINESS_PLAN.md`

---

**Happy detecting! 🎙️✨**
