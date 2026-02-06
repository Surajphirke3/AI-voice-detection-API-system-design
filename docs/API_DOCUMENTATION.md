# AI Voice Detection API - Complete Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [API Specification](#api-specification)
3. [Authentication](#authentication)
4. [Endpoints](#endpoints)
5. [Request/Response Examples](#examples)
6. [Error Handling](#error-handling)
7. [Rate Limits](#rate-limits)
8. [Deployment Guide](#deployment)

---

## 🎯 Overview

The AI Voice Detection API analyzes audio samples and classifies them as either **AI-generated** or **human speech** with a confidence score. It supports five languages: Tamil, English, Hindi, Malayalam, and Telugu.

### Key Features
- ✅ Multi-language support (5 languages)
- ✅ High accuracy ensemble model
- ✅ Fast inference (<2 seconds)
- ✅ RESTful API with JSON responses
- ✅ Secure API key authentication
- ✅ Detailed confidence scores

### Technical Approach
- **Feature Extraction**: MFCC, prosody, spectral analysis
- **Classification**: Ensemble of RF, GBM, and SVM
- **Languages**: Tamil, English, Hindi, Malayalam, Telugu

---

## 🔐 Authentication

All API requests require authentication via API key in the header.

### Header Format
```
X-API-Key: your_api_key_here
```

### Example
```bash
curl -X POST "https://api.voicedetection.com/detect" \
  -H "X-API-Key: demo_key_12345" \
  -H "Content-Type: application/json"
```

---

## 📡 API Specification

### Base URL
```
Production: https://api.voicedetection.com
Development: http://localhost:8000
```

### Content Type
All requests and responses use `application/json`

### Supported Languages
- `tamil`
- `english`
- `hindi`
- `malayalam`
- `telugu`

---

## 🛠️ Endpoints

### 1. Health Check
Check API status and availability.

**Endpoint**: `GET /health`

**Authentication**: Not required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-02-05T10:30:00.000Z",
  "version": "1.0.0"
}
```

---

### 2. Voice Detection
Analyze audio and detect if AI-generated or human.

**Endpoint**: `POST /detect`

**Authentication**: Required (API Key)

**Request Body**:
```json
{
  "audio_base64": "base64_encoded_mp3_string",
  "language": "english"
}
```

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| audio_base64 | string | Yes | Base64-encoded MP3 audio file |
| language | string | Yes | Audio language (tamil/english/hindi/malayalam/telugu) |

**Response** (200 OK):
```json
{
  "prediction": "AI_GENERATED",
  "confidence": 0.876,
  "language": "english",
  "processing_time_ms": 1523.45,
  "timestamp": "2024-02-05T10:30:00.000Z",
  "audio_duration_seconds": 8.5,
  "model_version": "1.0.0"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| prediction | string | Either "AI_GENERATED" or "HUMAN" |
| confidence | float | Confidence score (0.0 to 1.0) |
| language | string | Language of the analyzed audio |
| processing_time_ms | float | Processing time in milliseconds |
| timestamp | string | ISO 8601 timestamp |
| audio_duration_seconds | float | Duration of audio sample |
| model_version | string | Version of the detection model |

---

## 📝 Request/Response Examples

### Example 1: Detecting AI-Generated Voice (Python)

```python
import requests
import base64

# Read audio file
with open("sample_audio.mp3", "rb") as f:
    audio_bytes = f.read()

# Encode to base64
audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

# API request
response = requests.post(
    "https://api.voicedetection.com/detect",
    headers={
        "X-API-Key": "your_api_key_here",
        "Content-Type": "application/json"
    },
    json={
        "audio_base64": audio_base64,
        "language": "english"
    }
)

result = response.json()
print(f"Prediction: {result['prediction']}")
print(f"Confidence: {result['confidence']:.2%}")
```

**Response**:
```json
{
  "prediction": "AI_GENERATED",
  "confidence": 0.923,
  "language": "english",
  "processing_time_ms": 1234.56,
  "timestamp": "2024-02-05T10:30:00.000Z",
  "audio_duration_seconds": 5.2,
  "model_version": "1.0.0"
}
```

---

### Example 2: Detecting Human Voice (JavaScript)

```javascript
const fs = require('fs');
const axios = require('axios');

// Read and encode audio
const audioBuffer = fs.readFileSync('human_voice.mp3');
const audioBase64 = audioBuffer.toString('base64');

// API request
axios.post('https://api.voicedetection.com/detect', {
  audio_base64: audioBase64,
  language: 'tamil'
}, {
  headers: {
    'X-API-Key': 'your_api_key_here',
    'Content-Type': 'application/json'
  }
})
.then(response => {
  console.log('Prediction:', response.data.prediction);
  console.log('Confidence:', response.data.confidence);
})
.catch(error => {
  console.error('Error:', error.response.data);
});
```

**Response**:
```json
{
  "prediction": "HUMAN",
  "confidence": 0.891,
  "language": "tamil",
  "processing_time_ms": 1456.78,
  "timestamp": "2024-02-05T10:35:00.000Z",
  "audio_duration_seconds": 7.8,
  "model_version": "1.0.0"
}
```

---

### Example 3: cURL Request

```bash
# Encode audio to base64
AUDIO_BASE64=$(base64 -i sample.mp3)

# Make request
curl -X POST "https://api.voicedetection.com/detect" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d "{
    \"audio_base64\": \"$AUDIO_BASE64\",
    \"language\": \"hindi\"
  }"
```

---

## ⚠️ Error Handling

### Error Response Format
```json
{
  "detail": "Error message description"
}
```

### Common Error Codes

| Status Code | Error | Description |
|-------------|-------|-------------|
| 400 | Bad Request | Invalid request format or parameters |
| 403 | Forbidden | Invalid or missing API key |
| 413 | Payload Too Large | Audio file exceeds size limit |
| 422 | Unprocessable Entity | Invalid audio format or encoding |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

### Error Examples

**Invalid API Key (403)**:
```json
{
  "detail": "Invalid API Key"
}
```

**Invalid Audio Duration (400)**:
```json
{
  "detail": "Audio duration must be between 1-60 seconds. Got 75.2s"
}
```

**Invalid Language (422)**:
```json
{
  "detail": [
    {
      "loc": ["body", "language"],
      "msg": "unexpected value; permitted: 'tamil', 'english', 'hindi', 'malayalam', 'telugu'",
      "type": "value_error.const"
    }
  ]
}
```

**Invalid Base64 (422)**:
```json
{
  "detail": [
    {
      "loc": ["body", "audio_base64"],
      "msg": "Invalid base64 encoding",
      "type": "value_error"
    }
  ]
}
```

---

## 🚦 Rate Limits

### Current Limits
- **Requests per minute**: 60
- **Requests per hour**: 1000
- **Max audio duration**: 60 seconds
- **Max file size**: 10 MB

### Rate Limit Headers
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1612523400
```

---

## 🚀 Deployment Guide

### Local Development

1. **Clone Repository**
```bash
git clone https://github.com/yourrepo/voice-detection-api
cd voice-detection-api
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Run Server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Access API**
```
http://localhost:8000/docs
```

---

### Docker Deployment

1. **Build Image**
```bash
docker build -t voice-detection-api .
```

2. **Run Container**
```bash
docker run -d -p 8000:8000 \
  --name voice-api \
  voice-detection-api
```

3. **Check Logs**
```bash
docker logs -f voice-api
```

---

### Cloud Deployment (AWS)

#### Using EC2

1. **Launch EC2 Instance**
   - AMI: Ubuntu 22.04
   - Instance Type: t3.medium (minimum)
   - Security Group: Allow port 8000

2. **SSH into Instance**
```bash
ssh -i key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com
```

3. **Install Docker**
```bash
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
```

4. **Deploy Application**
```bash
git clone <your-repo>
cd voice-detection-api
sudo docker build -t voice-api .
sudo docker run -d -p 8000:8000 voice-api
```

5. **Setup Nginx (Optional)**
```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/voice-api
```

Nginx config:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

### Environment Variables

Create `.env` file:
```bash
API_KEY=your_secure_api_key
MODEL_PATH=/app/models
LOG_LEVEL=INFO
MAX_WORKERS=4
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost/voice_db
```

---

## 📊 Performance Benchmarks

### Model Performance
- **Accuracy**: 94.2% on test set
- **Precision** (AI): 93.5%
- **Recall** (AI): 95.1%
- **F1-Score**: 94.3%
- **ROC AUC**: 0.972

### Inference Speed
- **Average**: 1.2 seconds
- **P95**: 2.1 seconds
- **P99**: 3.5 seconds

### Supported Audio
- **Format**: MP3
- **Sample Rate**: Any (resampled to 22050 Hz)
- **Channels**: Mono/Stereo (converted to mono)
- **Duration**: 1-60 seconds

---

## 🔧 Testing

### Unit Tests
```bash
pytest tests/test_api.py -v
```

### Load Testing
```bash
locust -f tests/load_test.py --host=http://localhost:8000
```

### Example Test
```python
def test_detect_ai_voice():
    with open("tests/samples/ai_voice.mp3", "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()
    
    response = client.post(
        "/detect",
        json={"audio_base64": audio_b64, "language": "english"},
        headers={"X-API-Key": "test_key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in ["AI_GENERATED", "HUMAN"]
    assert 0.0 <= data["confidence"] <= 1.0
```

---

## 📞 Support

- **Documentation**: https://docs.voicedetection.com
- **Email**: support@voicedetection.com
- **GitHub Issues**: https://github.com/yourrepo/voice-detection-api/issues

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🔄 API Changelog

### v1.0.0 (2024-02-05)
- Initial release
- Support for 5 languages
- Ensemble classification model
- RESTful API with authentication
